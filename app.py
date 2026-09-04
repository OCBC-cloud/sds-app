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
    page_title="SDS Design Studio Pro v3.0 - Automatic Sizing",
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
    
    .image-thumbnail {
        border-radius: 8px;
        border: 1px solid #2a3a4f;
        padding: 0.5rem;
        background-color: #141e2b;
        text-align: center;
    }
    .image-thumbnail img {
        border-radius: 4px;
    }
    .image-popout {
        background-color: #0a0e17;
        border-radius: 12px;
        padding: 1rem;
        border: 2px solid #4a7a9c;
        text-align: center;
    }
    .image-popout img {
        max-width: 100%;
        border-radius: 8px;
    }
    
    .sizing-result {
        background-color: #1a2a3a;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border-left: 4px solid #f39c12;
    }
    .sizing-result-good {
        border-left-color: #2ecc71;
    }
    .sizing-result-warning {
        border-left-color: #f39c12;
    }
    .sizing-result-error {
        border-left-color: #e74c3c;
    }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# TRUSS TYPE ICONS
# ============================================================
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
# MATERIAL DATABASE
# ============================================================
STEEL_GRADES = {
    "S235": {"fy": 235, "fu": 360, "E": 210000, "density": 7850, "cost_per_kg": 0.90, "description": "General structural steel"},
    "S275": {"fy": 275, "fu": 430, "E": 210000, "density": 7850, "cost_per_kg": 1.00, "description": "Standard structural steel"},
    "S355": {"fy": 355, "fu": 490, "E": 210000, "density": 7850, "cost_per_kg": 1.20, "description": "High strength steel"},
    "S420": {"fy": 420, "fu": 520, "E": 210000, "density": 7850, "cost_per_kg": 1.50, "description": "Very high strength steel"},
    "S460": {"fy": 460, "fu": 550, "E": 210000, "density": 7850, "cost_per_kg": 1.80, "description": "Ultra-high strength steel"}
}

ALUMINUM_GRADES = {
    "6061-T6": {"fy": 276, "fu": 310, "E": 69000, "density": 2700, "cost_per_kg": 4.50, "description": "General purpose aluminum"},
    "6063-T6": {"fy": 214, "fu": 241, "E": 69000, "density": 2700, "cost_per_kg": 4.00, "description": "Architectural aluminum"},
    "5083-H116": {"fy": 230, "fu": 310, "E": 69000, "density": 2660, "cost_per_kg": 5.00, "description": "Marine grade aluminum"},
    "7022-T6": {"fy": 460, "fu": 510, "E": 69000, "density": 2780, "cost_per_kg": 8.00, "description": "High strength aluminum"}
}

WOOD_GRADES = {
    "Glulam": {"fy": 40, "fu": 55, "E": 12000, "density": 550, "cost_per_m3": 800, "description": "Glued laminated timber"},
    "LVL": {"fy": 45, "fu": 60, "E": 13500, "density": 600, "cost_per_m3": 700, "description": "Laminated veneer lumber"},
    "CLT": {"fy": 30, "fu": 45, "E": 10000, "density": 500, "cost_per_m3": 1200, "description": "Cross-laminated timber"},
    "Mass Timber": {"fy": 35, "fu": 50, "E": 11000, "density": 550, "cost_per_m3": 1000, "description": "Mass timber panels"}
}

COMPOSITE_GRADES = {
    "GFRP": {"fy": 300, "fu": 450, "E": 30000, "density": 2000, "cost_per_kg": 15.00, "description": "Glass fiber reinforced polymer"},
    "CFRP": {"fy": 600, "fu": 900, "E": 120000, "density": 1600, "cost_per_kg": 30.00, "description": "Carbon fiber reinforced polymer"}
}

# ============================================================
# ENHANCED SECTION PROPERTIES DATABASE
# ============================================================
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
    "Glulam 90x200": {"A": 18000, "I": 60.0e6, "W_el": 600e3, "i": 57.7, "weight": 9.9, "type": "Wood"},
    "Glulam 150x300": {"A": 45000, "I": 337.5e6, "W_el": 2250e3, "i": 86.6, "weight": 24.75, "type": "Wood"},
    "Glulam 200x400": {"A": 80000, "I": 1066.7e6, "W_el": 5333e3, "i": 115.5, "weight": 44.0, "type": "Wood"},
    "Aluminum 100x100x4": {"A": 1536, "I": 2.3e6, "W_el": 46e3, "i": 38.7, "weight": 4.15, "type": "Aluminum"},
    "Aluminum 150x150x5": {"A": 2900, "I": 8.1e6, "W_el": 108e3, "i": 52.8, "weight": 7.83, "type": "Aluminum"},
    "Aluminum 200x200x6": {"A": 4656, "I": 24.3e6, "W_el": 243e3, "i": 72.3, "weight": 12.57, "type": "Aluminum"},
}

# ============================================================
# IMAGE COMPRESSION FUNCTION
# ============================================================
def compress_image(uploaded_file, max_size=300, quality=65):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        width, height = img.size
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        
        new_width = max(100, new_width)
        new_height = max(100, new_height)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"⚠️ Error compressing image: {e}")
        return None

# ============================================================
# SHAPE FUNCTIONS
# ============================================================
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
    else:
        return rise * (1 - x_norm**2)

def generate_truss_members(x, z_beam, truss_type="warren", num_panels=4):
    members = []
    n = len(x)
    panel_size = max(1, n // num_panels)
    
    if truss_type == "warren":
        for i in range(0, n - panel_size, panel_size):
            j = min(i + panel_size, n - 1)
            members.append(("top", i, j))
            members.append(("bottom", i, j))
            members.append(("diag", i, j))
            members.append(("diag", j, i))
    elif truss_type == "pratt":
        for i in range(0, n - panel_size, panel_size):
            j = min(i + panel_size, n - 1)
            members.append(("top", i, j))
            members.append(("bottom", i, j))
            members.append(("vertical", i, j))
            members.append(("diag", i, j))
    elif truss_type == "howe":
        for i in range(0, n - panel_size, panel_size):
            j = min(i + panel_size, n - 1)
            members.append(("top", i, j))
            members.append(("bottom", i, j))
            members.append(("vertical", i, j))
            members.append(("diag", j, i))
    elif truss_type == "vierendeel":
        for i in range(0, n - panel_size, panel_size):
            j = min(i + panel_size, n - 1)
            members.append(("top", i, j))
            members.append(("bottom", i, j))
            members.append(("vertical", i, j))
    
    return members

# ============================================================
# AUTOMATIC SIZING ENGINE
# ============================================================
def calculate_required_section(force_kN, length_m, material_type, section_type="beam", compression=True):
    """
    Calculate required section properties based on force
    Returns: Suggested section size
    """
    
    # Get material properties
    if material_type == "Steel":
        fy = 355  # MPa (S355 default)
        E = 210000
    elif material_type == "Aluminum":
        fy = 276
        E = 69000
    elif material_type == "Wood":
        fy = 40
        E = 12000
    else:
        fy = 355
        E = 210000
    
    safety = 1.5
    
    # Calculate required area
    required_area = (abs(force_kN) * 1000 * safety) / fy  # mm²
    
    # Required second moment (approximate)
    M = abs(force_kN) * length_m / 6  # kNm
    required_I = (M * 1e6 * length_m * 12) / (E * 10)  # mm⁴
    
    # Search database
    best_section = None
    best_score = float('inf')
    
    # Filter sections by type if needed
    filtered_sections = SECTION_PROPERTIES.items()
    
    for section, props in filtered_sections:
        if props["A"] <= 0:
            continue
            
        # Calculate score
        area_score = abs(props["A"] - required_area) / required_area if required_area > 0 else 0
        i_score = abs(props["I"] - required_I) / required_I if required_I > 0 else 0
        
        # Weighted score
        total_score = area_score * 0.7 + i_score * 0.3
        
        # Penalize sections too small
        if props["A"] < required_area * 0.7:
            total_score += 10
        
        if total_score < best_score:
            best_score = total_score
            best_section = section
    
    if best_section and best_section in SECTION_PROPERTIES:
        props = SECTION_PROPERTIES[best_section]
        return {
            "section": best_section,
            "properties": props,
            "required_area": required_area,
            "required_I": required_I,
            "force_kN": abs(force_kN),
            "material": material_type,
            "capacity_ratio": props["A"] / required_area if required_area > 0 else 0,
            "is_adequate": props["A"] >= required_area * 0.8
        }
    
    return None

def size_all_members(params, materials):
    """Size all members of the structure automatically"""
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    
    # Calculate loads
    membrane_area = span * laa * 1.1
    wind_force = calculate_wind_load_from_standard(params, materials)
    dead_load = calculate_dead_load_from_section(params, materials)
    live_load = 0.5 * membrane_area / 10  # kN (reduced for preliminary)
    
    total_load = wind_force + dead_load + live_load
    
    # Forces in beams (simplified)
    beam_force = total_load * span / (4 * rise) * 1.5 if rise > 0 else total_load * 0.5
    
    member_type = materials.get("member_type", "single_beam")
    material_type = materials.get("material_type", "Steel")
    
    results = {
        "loads": {
            "wind": wind_force,
            "dead": dead_load,
            "live": live_load,
            "total": total_load
        },
        "beams": {},
        "truss": {}
    }
    
    if member_type == "single_beam":
        beam_result = calculate_required_section(
            beam_force, span, material_type, "beam"
        )
        if beam_result:
            results["beams"]["main"] = beam_result
            results["beams"]["selected"] = beam_result["section"]
        
    elif member_type == "planar_truss":
        top_force = beam_force * 1.2
        bottom_force = beam_force * 0.8
        diag_force = beam_force * 0.6
        vert_force = beam_force * 0.4
        
        top_result = calculate_required_section(top_force, span/4, material_type, "beam", compression=True)
        bottom_result = calculate_required_section(bottom_force, span/4, material_type, "beam", compression=False)
        diag_result = calculate_required_section(diag_force, span/6, material_type, "beam")
        vert_result = calculate_required_section(vert_force, span/8, material_type, "beam", compression=True)
        
        results["truss"]["top_chord"] = top_result if top_result else {"section": "N/A", "properties": {}, "force_kN": top_force}
        results["truss"]["bottom_chord"] = bottom_result if bottom_result else {"section": "N/A", "properties": {}, "force_kN": bottom_force}
        results["truss"]["diagonals"] = diag_result if diag_result else {"section": "N/A", "properties": {}, "force_kN": diag_force}
        results["truss"]["verticals"] = vert_result if vert_result else {"section": "N/A", "properties": {}, "force_kN": vert_force}
        results["truss"]["selected"] = {
            "top": top_result["section"] if top_result else "N/A",
            "bottom": bottom_result["section"] if bottom_result else "N/A",
            "diagonal": diag_result["section"] if diag_result else "N/A",
            "vertical": vert_result["section"] if vert_result else "N/A"
        }
        
    elif member_type == "space_truss":
        top_force = beam_force * 0.8
        bottom_force = beam_force * 0.6
        diag_force = beam_force * 0.4
        
        top_result = calculate_required_section(top_force, span/3, material_type, "beam", compression=True)
        bottom_result = calculate_required_section(bottom_force, span/3, material_type, "beam", compression=False)
        diag_result = calculate_required_section(diag_force, span/5, material_type, "beam")
        
        results["truss"]["top_chord"] = top_result if top_result else {"section": "N/A", "properties": {}, "force_kN": top_force}
        results["truss"]["bottom_chord"] = bottom_result if bottom_result else {"section": "N/A", "properties": {}, "force_kN": bottom_force}
        results["truss"]["diagonals"] = diag_result if diag_result else {"section": "N/A", "properties": {}, "force_kN": diag_force}
        results["truss"]["selected"] = {
            "top": top_result["section"] if top_result else "N/A",
            "bottom": bottom_result["section"] if bottom_result else "N/A",
            "diagonal": diag_result["section"] if diag_result else "N/A"
        }
    
    return results

def calculate_wind_load_from_standard(params, materials):
    """Calculate wind load based on selected standard"""
    span = params.get("B", 10.0)
    laa = params.get("LAA", 15.0)
    standard = materials.get("standard", "EU")
    
    membrane_area = span * laa * 1.1
    
    # Wind speed per standard
    if standard == "MY":
        wind_speed = 33.5
    elif standard == "EU":
        wind_speed = 30.0
    elif standard == "CN":
        wind_speed = 28.0
    elif standard == "UK":
        wind_speed = 26.0
    elif standard == "US":
        wind_speed = 38.0
    else:
        wind_speed = 30.0
    
    rho = 1.225
    q = 0.5 * rho * wind_speed**2 / 1000
    wind_pressure = q * 1.2
    wind_force = wind_pressure * membrane_area
    
    return wind_force

def calculate_dead_load_from_section(params, materials):
    """Calculate dead load from section properties"""
    span = params.get("B", 10.0)
    laa = params.get("LAA", 15.0)
    section = materials.get("section_size", "CHS 168.3x7.1")
    
    section_data = SECTION_PROPERTIES.get(section, SECTION_PROPERTIES["CHS 168.3x7.1"])
    
    # Steel/fabric weight
    steel_weight = section_data.get("weight", 28.3) * span * 2 / 100  # kN
    membrane_area = span * laa * 1.1
    fabric_weight = 1.2 * membrane_area / 100  # kN
    
    return steel_weight + fabric_weight

def render_automatic_sizing(params, materials, sizing_results):
    """Display automatic sizing results with visual feedback"""
    
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">🧠 Automatic Member Sizing</div>', unsafe_allow_html=True)
    
    st.success("✅ System has automatically sized all members based on loads and spans")
    
    # Loads summary
    loads = sizing_results["loads"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Wind Load", f"{loads['wind']:.1f} kN")
    with col2:
        st.metric("Dead Load", f"{loads['dead']:.1f} kN")
    with col3:
        st.metric("Live Load", f"{loads['live']:.1f} kN")
    with col4:
        st.metric("Total Load", f"{loads['total']:.1f} kN")
    
    st.markdown("---")
    
    member_type = materials.get("member_type", "single_beam")
    
    if member_type == "single_beam":
        beam = sizing_results["beams"].get("main")
        if beam:
            st.markdown("#### 📐 Single Beam Sizing")
            
            col1, col2 = st.columns(2)
            with col1:
                status = "✅" if beam["is_adequate"] else "⚠️"
                st.markdown(f"**Selected Section:** {status} **{beam['section']}**")
                st.write(f"**Area:** {beam['properties'].get('A', 0):.0f} mm²")
                st.write(f"**Weight:** {beam['properties'].get('weight', 0):.1f} kg/m")
                st.write(f"**Second Moment:** {beam['properties'].get('I', 0)/1e6:.1f} cm⁴")
            with col2:
                st.write(f"**Force:** {beam['force_kN']:.1f} kN")
                st.write(f"**Required Area:** {beam['required_area']:.0f} mm²")
                st.write(f"**Capacity Ratio:** {beam['capacity_ratio']:.2f}")
                st.write(f"**Material:** {beam['material']}")
            
            if beam["is_adequate"]:
                st.success(f"✅ Recommended: {beam['section']} (Adequate)")
            else:
                st.warning(f"⚠️ Consider larger section. Current: {beam['section']} (Under-sized)")
        else:
            st.warning("⚠️ No suitable section found. Consider larger members or higher grade material.")
            
    elif member_type in ["planar_truss", "space_truss"]:
        truss = sizing_results["truss"]
        
        st.markdown("#### 📐 Truss Member Sizing")
        
        data = []
        
        # Top chord
        top = truss.get("top_chord", {})
        data.append({
            "Member": "Top Chord",
            "Section": top.get("section", "N/A"),
            "Area (mm²)": top.get("properties", {}).get("A", 0) if top else 0,
            "Force (kN)": top.get("force_kN", 0) if top else 0,
            "Status": "✅" if top.get("is_adequate", False) else "⚠️" if top else "N/A"
        })
        
        # Bottom chord
        bottom = truss.get("bottom_chord", {})
        data.append({
            "Member": "Bottom Chord",
            "Section": bottom.get("section", "N/A"),
            "Area (mm²)": bottom.get("properties", {}).get("A", 0) if bottom else 0,
            "Force (kN)": bottom.get("force_kN", 0) if bottom else 0,
            "Status": "✅" if bottom.get("is_adequate", False) else "⚠️" if bottom else "N/A"
        })
        
        # Diagonals
        diag = truss.get("diagonals", {})
        data.append({
            "Member": "Diagonals",
            "Section": diag.get("section", "N/A"),
            "Area (mm²)": diag.get("properties", {}).get("A", 0) if diag else 0,
            "Force (kN)": diag.get("force_kN", 0) if diag else 0,
            "Status": "✅" if diag.get("is_adequate", False) else "⚠️" if diag else "N/A"
        })
        
        # Verticals (if planar truss)
        if "verticals" in truss:
            vert = truss.get("verticals", {})
            data.append({
                "Member": "Verticals",
                "Section": vert.get("section", "N/A"),
                "Area (mm²)": vert.get("properties", {}).get("A", 0) if vert else 0,
                "Force (kN)": vert.get("force_kN", 0) if vert else 0,
                "Status": "✅" if vert.get("is_adequate", False) else "⚠️" if vert else "N/A"
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Summary
        all_adequate = all("✅" in str(row["Status"]) for row in data)
        if all_adequate:
            st.success(f"✅ All truss members are adequately sized")
        else:
            st.warning("⚠️ Some members may be under-sized. Consider increasing section sizes.")
        
        # Visual summary
        selected = truss.get("selected", {})
        st.info(f"**Recommended:** Top: {selected.get('top', 'N/A')} | Bottom: {selected.get('bottom', 'N/A')} | Diagonal: {selected.get('diagonal', 'N/A')}")
    
    # Apply button
    if st.button("✅ Apply Automatic Sizing", use_container_width=True, type="primary"):
        member_type = materials.get("member_type", "single_beam")
        
        if member_type == "single_beam":
            beam = sizing_results["beams"].get("main")
            if beam and beam.get("section"):
                materials["section_size"] = beam["section"]
                st.success(f"✅ Applied: {beam['section']}")
                st.rerun()
        elif member_type in ["planar_truss", "space_truss"]:
            truss = sizing_results["truss"]
            selected = truss.get("selected", {})
            top = selected.get("top", "N/A")
            if top != "N/A":
                materials["section_size"] = top
                st.success(f"✅ Applied top chord: {top}")
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_reaction_forces(params, materials):
    """Display support reactions and ground anchor forces"""
    
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">🔧 Reaction Forces & Anchors</div>', unsafe_allow_html=True)
    
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    
    # Get section properties
    section = materials.get("section_size", "CHS 168.3x7.1")
    section_data = SECTION_PROPERTIES.get(section, SECTION_PROPERTIES["CHS 168.3x7.1"])
    
    # Calculate loads
    membrane_area = span * laa * 1.1
    
    # Wind load
    wind_force = calculate_wind_load_from_standard(params, materials)
    
    # Dead load
    dead_load = calculate_dead_load_from_section(params, materials)
    
    # Total load
    total_load = wind_force + dead_load
    
    # Support reactions
    num_supports = 4
    vertical_reaction = (total_load) / num_supports
    horizontal_reaction = wind_force * 0.6 / num_supports
    
    # Tie-down forces
    num_bays = materials.get("num_bays", 2)
    num_anchors = num_bays * 4
    vertical_angle = materials.get("tie_down_vertical_angle", 45)
    
    uplift_per_anchor = (wind_force * 0.5) / num_anchors if num_anchors > 0 else 0
    cable_force = uplift_per_anchor / np.cos(np.radians(vertical_angle))
    
    # Cable check
    cable_type = materials.get("wire_rope_type", "6x19 Galvanized")
    cable_diameter = materials.get("wire_rope_diameter", 12)
    
    cable_breaking = {6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140, 18: 180, 20: 220}
    breaking_load = cable_breaking.get(cable_diameter, 80)
    safety_factor = cable_force / breaking_load if breaking_load > 0 else 0
    
    # Display
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
        
        # Safety factor with color
        if safety_factor < 0.7:
            st.success(f"✅ Safety Factor: {safety_factor:.2f} (Adequate)")
        else:
            st.warning(f"⚠️ Safety Factor: {safety_factor:.2f} (Check required)")
    
    # Summary table
    st.markdown("#### 📋 Summary")
    summary_data = {
        "Parameter": ["Wind Speed", "Wind Load", "Dead Load", "Vertical Reaction", "Cable Tension", "Safety Factor"],
        "Value": [
            f"{calculate_wind_load_from_standard(params, materials) / (span * laa * 1.1):.1f} m/s",
            f"{wind_force:.1f} kN",
            f"{dead_load:.1f} kN",
            f"{vertical_reaction:.1f} kN",
            f"{cable_force:.1f} kN",
            f"{safety_factor:.2f}"
        ]
    }
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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
if "show_image_popout" not in st.session_state:
    st.session_state.show_image_popout = None
if "project_save_path" not in st.session_state:
    st.session_state.project_save_path = None

# Materials State
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
        "custom_prestress": 3.0,
        "auto_sizing_applied": False
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
            st.session_state.show_image_popout = None
            st.session_state.project_save_path = filepath
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
    st.session_state.show_image_popout = None
    st.session_state.project_save_path = None
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
        st.session_state.project_info["reference"] = ref
    
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
        "comments": st.session_state.comments,
        "materials": st.session_state.materials,
        "selected_standard": st.session_state.selected_standard
    }
    
    if existing_file:
        filepath = os.path.join(CACHE_DIR, existing_file)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        st.session_state.project_save_path = filepath
        st.success(f"✅ Project updated: {st.session_state.project_info.get('name')}")
    else:
        filename = f"project_{ref}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(CACHE_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        st.session_state.project_save_path = filepath
        st.success(f"✅ Project saved: {st.session_state.project_info.get('name')}")
    
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
# STANDARD FUNCTIONS
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
# 3D GENERATOR
# ============================================================
def generate_saddle_span(params, materials=None):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    num_points = 50

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    shape_type = materials.get("shape_type", "parabolic") if materials else "parabolic"
    member_type = materials.get("member_type", "single_beam") if materials else "single_beam"
    truss_type = materials.get("truss_type", "warren") if materials else "warren"
    anchoring_pattern = materials.get("anchoring_pattern", "standard") if materials else "standard"
    prestress_level = materials.get("prestress_level", "medium") if materials else "medium"
    
    prestress_values = {"none": 0, "low": 1.5, "medium": 3.0, "high": 5.0}
    if prestress_level == "custom":
        prestress = materials.get("custom_prestress", 3.0) if materials else 3.0
    else:
        prestress = prestress_values.get(prestress_level, 3.0)

    x = np.linspace(-span/2, span/2, num_points)
    z_beam = get_beam_shape(x, span, rise, shape_type)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    fig = go.Figure()

    # ===== DRAW BEAMS/TRUSSES =====
    if member_type == "single_beam":
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
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode='lines', name='Beam 1 (Truss)',
            line=dict(color='#FF6B6B', width=5)
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode='lines', name='Beam 2 (Truss)',
            line=dict(color='#FF6B6B', width=5)
        ))
        
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
        
        for i in range(0, num_points - 5, 5):
            idx = i
            idx_next = min(i + 5, num_points - 1)
            if idx != idx_next:
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
        
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            y1_pos = y1[idx]
            y2_pos = y2[idx]
            z_pos = z_beam[idx]
            
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[y1_pos, y2_pos], z=[z_pos, z_pos],
                mode='lines', name='Bracing',
                line=dict(color='#FF6B6B', width=3, dash='dash'),
                showlegend=False
            ))
        
        if anchoring_pattern == "standard":
            anchor_x_positions = bracing_x
        elif anchoring_pattern == "continuous":
            anchor_x_positions = np.linspace(-span/2 * 0.8, span/2 * 0.8, num_bays * 4).tolist()
        elif anchoring_pattern == "hybrid":
            extra_points = []
            for i in range(len(bracing_x) - 1):
                mid = (bracing_x[i] + bracing_x[i+1]) / 2
                extra_points.append(mid)
            anchor_x_positions = sorted(bracing_x + extra_points)
        else:
            anchor_x_positions = bracing_x
        
        tie_down_anchors = calculate_tie_down_positions(
            span, laa, rise, anchor_x_positions, vertical_angle, horizontal_spread
        )
        
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
# OTHER GENERATORS
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
# HEALTH REPORT FUNCTIONS
# ============================================================
def calculate_steel_capacity_standard(grade, section, length, safety_factor, standard="EU", material_type="Steel"):
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
    span = params.get("B", 10.0)
    laa = params.get("LAA", 15.0)
    rise = params.get("A", 6.0)
    
    m = materials
    standard = m.get("standard", "EU")
    
    wind_force = calculate_wind_load_from_standard(params, materials)
    dead_load = calculate_dead_load_from_section(params, materials)
    
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
    total_load = wind_force + dead_load
    
    num_anchors = m.get("num_bays", 2) * 4
    tie_down_force = (wind_force * 0.5) / num_anchors if num_anchors > 0 else 0
    
    cable_selection = calculate_cable_size_standard(
        tie_down_force,
        m.get("safety_factor", 1.5),
        m.get("wire_rope_type", "6x19 Galvanized")
    )
    
    health_score = 100
    
    if wind_force > 100:
        health_score -= 15
    elif wind_force > 50:
        health_score -= 8
    
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
            "wind_check": wind_force < 80,
            "steel_capacity_check": steel_capacity["efficiency"] > 0.5,
            "cable_adequacy_check": cable_selection["is_adequate"],
            "slenderness_check": steel_capacity["slenderness"] < 100
        }
    }

# ============================================================
# IMAGE GALLERY FUNCTION
# ============================================================
def render_image_gallery():
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">📸 Image Gallery</div>', unsafe_allow_html=True)
    
    ref = st.session_state.project_info.get("reference", "")
    if not ref:
        st.info("💡 Save the project first to upload and store images.")
        return
    
    project_folder = os.path.join(".sds_cache", "projects", ref, "images")
    os.makedirs(project_folder, exist_ok=True)
    
    st.caption("Upload reference images (auto-compressed to ~0.5MB, max 300px)")
    
    uploaded_file = st.file_uploader(
        "Choose image to upload",
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
                st.warning(f"⚠️ Image '{filename}' already exists. Delete it first.")
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

# ============================================================
# UI FUNCTIONS
# ============================================================
def render_structural_health_report(report):
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
        st.metric("Wind Load", "✅ PASS" if checks["wind_check"] else "❌ FAIL")
    with col2:
        st.metric("Steel Capacity", "✅ PASS" if checks["steel_capacity_check"] else "❌ FAIL")
    with col3:
        st.metric("Cable Adequacy", "✅ PASS" if checks["cable_adequacy_check"] else "❌ FAIL")
    with col4:
        st.metric("Slenderness", "✅ PASS" if checks["slenderness_check"] else "⚠️ CHECK")
    
    st.markdown("---")
    
    st.subheader("🏗️ Member Capacity")
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
    st.title("🏗️ SDS Design Studio Pro v3.0")
    st.caption("🚀 Automatic Member Sizing | Saddle Span | Shape, Member Type, Material Options")
    
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
            <div class="icon">🧠</div>
            <div class="value">Auto</div>
            <div class="label">Sizing Engine</div>
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
    
    # Single Health Report Button
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
        
        # Truss type with icons
        if materials["member_type"] in ["planar_truss", "space_truss"]:
            truss_options = ["warren", "pratt", "howe", "vierendeel"]
            truss_labels = ["Warren", "Pratt", "Howe", "Vierendeel"]
            current_truss = materials.get("truss_type", "warren")
            if current_truss not in truss_options:
                current_truss = "warren"
            truss_idx = truss_options.index(current_truss) if current_truss in truss_options else 0
            
            truss_display = []
            for t in truss_options:
                icon = TRUSS_ICONS.get(t, "")
                label = TRUSS_LABELS.get(t, t)
                truss_display.append(f"{icon} {label}")
            
            selected_truss = st.selectbox(
                "Truss Type",
                truss_display,
                index=truss_idx,
                key="truss_select",
                help="Select truss configuration - icons show pattern"
            )
            
            selected_index = truss_display.index(selected_truss)
            materials["truss_type"] = truss_options[selected_index]
            
            st.caption(f"💡 {TRUSS_DESCRIPTIONS.get(materials['truss_type'], '')}")
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
            
        else:
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
        
        # Section Size - WITH AUTOMATIC SIZING
        st.markdown("#### 📐 Section Size")
        
        # Check if auto-sizing has been applied
        if materials.get("auto_sizing_applied", False):
            st.success(f"✅ Auto-sized: {materials.get('section_size', 'CHS 168.3x7.1')}")
            st.caption("System automatically selected this section based on load calculations")
        
        section_options = list(SECTION_PROPERTIES.keys())
        current_section = materials.get("section_size", "CHS 168.3x7.1")
        if current_section not in section_options:
            current_section = "CHS 168.3x7.1"
        
        materials["section_size"] = st.selectbox(
            "Section Size (or use Auto-Sizing below)",
            section_options,
            index=section_options.index(current_section),
            key="section_select"
        )
        
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
            st.caption("📊 Use top button")
        with col_act4:
            if st.button("📋 New", use_container_width=True, key="new_btn"):
                go_to_dashboard()
                st.rerun()
        with col_act5:
            if st.button("🏠 Home", use_container_width=True, key="home_btn"):
                go_to_dashboard()
                st.rerun()
        
        # ===== AUTOMATIC SIZING =====
        # Generate sizing results
        sizing_results = size_all_members(params, materials)
        render_automatic_sizing(params, materials, sizing_results)
        
        # ===== IMAGE GALLERY =====
        render_image_gallery()
        
        # ===== REACTION FORCES =====
        render_reaction_forces(params, materials)
    
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
    st.caption("📊 Use top")

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

# Typology Selection
if st.session_state.typology is None:
    st.subheader("Choose a structure type:")
    st.caption("🏕️ Saddle Span - Complete Module with Automatic Sizing")
    
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
st.caption("SDS Design Studio Pro v3.0 | 🧠 Automatic Member Sizing | MS EN 1991-1-4 Wind: 33.5m/s | Reaction Forces Displayed")

save_cache()
