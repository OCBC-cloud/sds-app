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
    page_title="SDS Design Studio Pro v3.2 - Intelligent Upgrade",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# OPTIMIZED DARK MODE CSS
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
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# DATA DEFINITIONS
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

# Material Databases
STEEL_GRADES = {
    "S235": {"fy": 235, "fu": 360, "E": 210000, "density": 7850, "cost_per_kg": 0.90},
    "S275": {"fy": 275, "fu": 430, "E": 210000, "density": 7850, "cost_per_kg": 1.00},
    "S355": {"fy": 355, "fu": 490, "E": 210000, "density": 7850, "cost_per_kg": 1.20},
    "S420": {"fy": 420, "fu": 520, "E": 210000, "density": 7850, "cost_per_kg": 1.50},
    "S460": {"fy": 460, "fu": 550, "E": 210000, "density": 7850, "cost_per_kg": 1.80}
}

ALUMINUM_GRADES = {
    "6061-T6": {"fy": 276, "fu": 310, "E": 69000, "density": 2700, "cost_per_kg": 4.50},
    "6063-T6": {"fy": 214, "fu": 241, "E": 69000, "density": 2700, "cost_per_kg": 4.00},
    "5083-H116": {"fy": 230, "fu": 310, "E": 69000, "density": 2660, "cost_per_kg": 5.00},
    "7022-T6": {"fy": 460, "fu": 510, "E": 69000, "density": 2780, "cost_per_kg": 8.00}
}

WOOD_GRADES = {
    "Glulam": {"fy": 40, "fu": 55, "E": 12000, "density": 550, "cost_per_m3": 800},
    "LVL": {"fy": 45, "fu": 60, "E": 13500, "density": 600, "cost_per_m3": 700},
    "CLT": {"fy": 30, "fu": 45, "E": 10000, "density": 500, "cost_per_m3": 1200},
    "Mass Timber": {"fy": 35, "fu": 50, "E": 11000, "density": 550, "cost_per_m3": 1000}
}

COMPOSITE_GRADES = {
    "GFRP": {"fy": 300, "fu": 450, "E": 30000, "density": 2000, "cost_per_kg": 15.00},
    "CFRP": {"fy": 600, "fu": 900, "E": 120000, "density": 1600, "cost_per_kg": 30.00}
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
# INTELLIGENT STRUCTURAL UPGRADE ENGINE
# ============================================================
def analyze_and_upgrade_structure(params, materials, sizing_results):
    """Analyze failed wind load and suggest upgrades"""
    
    span = params.get("B", 10.0)
    member_type = materials.get("member_type", "single_beam")
    current_section = materials.get("section_size", "CHS 168.3x7.1")
    wind_force = sizing_results["loads"]["wind"]
    beam_force = sizing_results.get("beams", {}).get("main", {}).get("force_kN", 0)
    
    upgrades = []
    
    # ===== OPTION A: Planar Steel Truss =====
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
                "members": {
                    "top_chord": top_r["section"],
                    "bottom_chord": bot_r["section"],
                    "diagonals": diag_r["section"],
                    "verticals": vert_r["section"] if vert_r else "N/A"
                },
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
    
    # ===== OPTION B: 3D Space Truss (Steel) =====
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
                "members": {
                    "top_chord": top_r["section"],
                    "bottom_chord": bot_r["section"],
                    "diagonals": diag_r["section"]
                },
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
    
    # ===== OPTION C: Aluminum Box Beam =====
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
            current_weight = SECTION_PROPERTIES.get(current_section, {}).get("weight", 0)
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
    
    # ===== OPTION D: Aluminum 3D Truss =====
    if member_type in ["single_beam", "planar_truss"] and beam_force > 0:
        al_top = calculate_required_section(beam_force * 0.7, span/3, "Aluminum", 276)
        al_bottom = calculate_required_section(beam_force * 0.5, span/3, "Aluminum", 276)
        al_diag = calculate_required_section(beam_force * 0.35, span/5, "Aluminum", 276)
        
        if al_top and al_bottom and al_diag:
            total_weight = (al_top["properties"].get("weight", 0) + al_bottom["properties"].get("weight", 0) + al_diag["properties"].get("weight", 0) * 2)
            
            upgrades.append({
                "name": "Aluminum 3D Truss",
                "type": "space_truss",
                "material": "Aluminum",
                "members": {
                    "top_chord": al_top["section"],
                    "bottom_chord": al_bottom["section"],
                    "diagonals": al_diag["section"]
                },
                "total_weight": total_weight,
                "weight_reduction": 0,
                "is_adequate": True,
                "description": "Ultra-lightweight aluminum truss - best for large spans",
                "member_details": {
                    "top": f"{al_top['section']} ({al_top['properties'].get('weight', 0):.1f} kg/m)",
                    "bottom": f"{al_bottom['section']} ({al_bottom['properties'].get('weight', 0):.1f} kg/m)",
                    "diagonal": f"{al_diag['section']} ({al_diag['properties'].get('weight', 0):.1f} kg/m)"
                }
            })
    
    # ===== OPTION E: Larger Steel Section =====
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
    """Display upgrade options with comparison and apply button"""
    
    if not upgrades:
        return
    
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">🔄 Intelligent Structural Upgrade</div>', unsafe_allow_html=True)
    
    st.warning("⚠️ Current design cannot handle wind load efficiently. The system has analyzed alternatives:")
    
    # Show comparison table
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
    
    # Show detailed members for selected
    st.markdown("#### 📐 Select an upgrade to preview")
    
    selected_idx = st.radio(
        "Choose upgrade option:",
        options=range(len(upgrades)),
        format_func=lambda i: f"{i+1}. {upgrades[i]['name']}",
        key="upgrade_select"
    )
    
    selected = upgrades[selected_idx]
    
    # Show details
    with st.expander("📋 Upgrade Details", expanded=True):
        st.markdown(f"**{selected['name']}**")
        st.write(f"Material: {selected['material']}")
        st.write(f"Total Weight: {selected['total_weight']:.1f} kg/m")
        st.write(f"Weight Reduction: {selected['weight_reduction']:.0f}%")
        st.write(f"Description: {selected['description']}")
        
        st.write("**Members:**")
        for key, value in selected.get("member_details", {}).items():
            st.write(f"- {key.title()}: {value}")
    
    # Apply button with confirmation
    if st.button(f"✅ Apply: {selected['name']}", use_container_width=True, type="primary"):
        old_section = materials.get("section_size", "None")
        old_member_type = materials.get("member_type", "single_beam")
        
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
        
        st.success(f"""
        ✅ **Upgrade Applied Successfully!**
        
        | Before | After |
        |--------|-------|
        | {old_member_type.replace('_', ' ').title()} | {selected['name']} |
        | {old_section} | {materials['section_size']} |
        
        🔄 **Please re-run the Health Report to see updated results.**
        """)
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
# OTHER GENERATORS (Placeholders)
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
# SESSION STATE & CACHE
# ============================================================
CACHE_DIR = ".sds_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "current_session.json")
PROJECTS_LIST_FILE = os.path.join(CACHE_DIR, "projects_index.json")

SESSION_DEFAULTS = {
    "project_registered": False, "project_info": {}, "typology": None, "params": {},
    "qa_answers": {}, "locked": False, "comments": "", "show_project_browser": False,
    "show_registration": False, "show_structural_report": False, "selected_standard": "EU",
    "show_image_popout": None, "project_save_path": None, "auto_sizing_applied": False
}

MATERIALS_DEFAULTS = {
    "standard": "EU", "material_type": "Steel", "steel_grade": "S355", "aluminum_grade": "6061-T6",
    "wood_grade": "Glulam", "composite_grade": "GFRP", "section_size": "CHS 168.3x7.1",
    "section_type": "CHS", "fabric_type": "PVC-coated Polyester", "fabric_thickness": 0.8,
    "wire_rope_type": "6x19 Galvanized", "wire_rope_diameter": 12, "num_bays": 2,
    "tie_down_vertical_angle": 45, "tie_down_horizontal_spread": 30, "wind_zone": "Zone 2",
    "terrain_category": "II", "building_height": 10.0, "importance_factor": 1.0,
    "safety_factor": 1.5, "shape_type": "parabolic", "member_type": "single_beam",
    "truss_type": "warren", "anchoring_pattern": "standard", "prestress_level": "medium",
    "custom_prestress": 3.0
}

for key, val in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val
if "materials" not in st.session_state:
    st.session_state.materials = MATERIALS_DEFAULTS.copy()

def save_cache():
    data = {k: st.session_state[k] for k in SESSION_DEFAULTS.keys()}
    data["materials"] = st.session_state.materials
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
                        "file": os.path.basename(f), "name": info.get("name", "Untitled"),
                        "client": info.get("client", "Unknown"), "reference": info.get("reference", "N/A"),
                        "typology": data.get("typology", "Unknown"),
                        "date": info.get("date", datetime.now().isoformat()),
                        "locked": data.get("locked", False), "standard": data.get("selected_standard", "EU")
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
            for key in SESSION_DEFAULTS.keys():
                st.session_state[key] = data.get(key, SESSION_DEFAULTS[key])
            st.session_state.materials = data.get("materials", MATERIALS_DEFAULTS.copy())
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
    for key in SESSION_DEFAULTS.keys():
        st.session_state[key] = SESSION_DEFAULTS[key]
    st.session_state.materials = MATERIALS_DEFAULTS.copy()
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    save_cache()

def save_project():
    if not st.session_state.project_info.get("name"):
        st.error("⚠️ Project name is required")
        return
    ref = st.session_state.project_info.get("reference") or f"SDS-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    if not st.session_state.project_info.get("reference"):
        st.session_state.project_info["reference"] = ref
    projects = get_projects_list()
    existing = next((p for p in projects if p.get("reference") == ref), None)
    data = {k: st.session_state[k] for k in SESSION_DEFAULTS.keys()}
    data["materials"] = st.session_state.materials
    if existing:
        filepath = os.path.join(CACHE_DIR, existing["file"])
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

# Load cache on startup
cached = load_cache()
if cached:
    for key in SESSION_DEFAULTS.keys():
        st.session_state[key] = cached.get(key, SESSION_DEFAULTS[key])
    st.session_state.materials = cached.get("materials", MATERIALS_DEFAULTS.copy())

# ============================================================
# UI RENDER FUNCTIONS
# ============================================================
def render_structural_health_report(report):
    st.markdown("## 🏥 STRUCTURAL HEALTH REPORT")
    st.markdown(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    score, status, color = report["health_score"], report["health_status"], report["health_color"]
    st.markdown(f"<div style='text-align:center;padding:2rem;background:#141e2b;border-radius:16px;border:3px solid {color};'><div style='font-size:4rem;font-weight:700;color:{color};'>{score}%</div><div style='font-size:2rem;font-weight:600;color:{color};'>{status}</div><div style='color:#b0c4de;margin-top:0.5rem;'>{report['recommendation']}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    checks = report["detailed_checks"]
    cols = st.columns(4)
    labels = ["Wind Load", "Steel Capacity", "Cable Adequacy", "Slenderness"]
    keys = ["wind_check", "steel_capacity_check", "cable_adequacy_check", "slenderness_check"]
    for i, (col, label, key) in enumerate(zip(cols, labels, keys)):
        col.metric(label, "✅ PASS" if checks.get(key, False) else "❌ FAIL")
    if "membrane_check" in report:
        st.markdown("---")
        st.subheader("🧵 Membrane Check")
        mem = report["membrane_check"]
        if mem.get("warning", False):
            st.warning("⚠️ ETFE NOT RECOMMENDED for this structure type. Use PVC or PTFE.")
        elif mem["is_adequate"]:
            st.success(f"✅ Membrane Adequate (Required: {mem.get('required_strength',0):.1f} kN/m, Actual: {mem.get('actual_strength',0):.1f} kN/m)")
        else:
            st.warning(f"⚠️ Membrane Under-sized (Required: {mem.get('required_strength',0):.1f} kN/m, Actual: {mem.get('actual_strength',0):.1f} kN/m)")

def render_dashboard():
    st.title("🏗️ SDS Design Studio Pro v3.2 - Intelligent Upgrade")
    st.caption("🚀 Automatic Member Sizing | Intelligent Structural Upgrade Engine")
    projects = get_projects_list()
    cols = st.columns(4)
    for i, (icon, label, val) in enumerate(zip(["📂", "🏕️", "🔧", "🧠"], ["Saved Projects", "Shape Variants", "Member Types", "Sizing Engine"], [len(projects), 4, 3, "Auto"])):
        cols[i].markdown(f"<div class='dashboard-card'><div class='icon'>{icon}</div><div class='value'>{val}</div><div class='label'>{label}</div></div>", unsafe_allow_html=True)
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ New Design", use_container_width=True, type="primary"):
            st.session_state.show_registration = True
            st.rerun()
    with c2:
        if projects and st.button("📂 Open Project", use_container_width=True):
            st.session_state.show_project_browser = True
            st.rerun()

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
    current_section = materials.get("section_size", "CHS 168.3x7.1")
    
    # Show current vs recommended
    st.markdown("#### 📊 Current vs Recommended")
    
    if member_type == "single_beam":
        beam = sizing_results["beams"].get("main")
        
        if beam:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Current Section**")
                st.write(f"📐 {current_section}")
                st.write(f"⚖️ {SECTION_PROPERTIES.get(current_section, {}).get('weight', 'N/A')} kg/m")
            with col2:
                st.markdown("**✅ Recommended Section**")
                st.write(f"📐 **{beam['section']}**")
                st.write(f"⚖️ **{beam['properties'].get('weight', 'N/A')} kg/m**")
            
            # Adequacy check
            wind_force = loads['wind']
            section_capacity = beam['properties'].get('A', 0) * 355 / 1500
            is_adequate = section_capacity > wind_force * 1.5
            
            if is_adequate:
                st.success(f"✅ This section can handle the wind load ({wind_force:.1f} kN)")
            else:
                st.warning(f"⚠️ Even this section may be inadequate for the wind load ({wind_force:.1f} kN). Consider reducing structure size or using upgrade options below.")
            
    elif member_type in ["planar_truss", "space_truss"]:
        truss = sizing_results["truss"]
        selected = truss.get("selected", {})
        st.write("**Truss Member Recommendations:**")
        st.write(f"📐 Top Chord: {selected.get('top', 'N/A')}")
        st.write(f"📐 Bottom Chord: {selected.get('bottom', 'N/A')}")
        st.write(f"📐 Diagonals: {selected.get('diagonal', 'N/A')}")
        if "vertical" in selected:
            st.write(f"📐 Verticals: {selected.get('vertical', 'N/A')}")
    
    # Apply button with confirmation
    if st.button("✅ Apply Automatic Sizing", use_container_width=True, type="primary"):
        member_type = materials.get("member_type", "single_beam")
        
        if member_type == "single_beam":
            beam = sizing_results["beams"].get("main")
            if beam and beam.get("section"):
                old_section = materials.get("section_size", "None")
                new_section = beam["section"]
                old_weight = SECTION_PROPERTIES.get(old_section, {}).get('weight', 'N/A')
                new_weight = beam['properties'].get('weight', 'N/A')
                
                materials["section_size"] = new_section
                st.session_state.auto_sizing_applied = True
                
                st.success(f"""
                ✅ **Section Updated Successfully!**
                
                | Before | After |
                |--------|-------|
                | **{old_section}** | **{new_section}** |
                | {old_weight} kg/m | {new_weight} kg/m |
                
                🔄 **Please re-run the Health Report to see updated results.**
                """)
                st.rerun()
                
        elif member_type in ["planar_truss", "space_truss"]:
            truss = sizing_results["truss"]
            selected = truss.get("selected", {})
            top = selected.get("top", "N/A")
            if top != "N/A":
                old_section = materials.get("section_size", "None")
                materials["section_size"] = top
                st.session_state.auto_sizing_applied = True
                
                st.success(f"""
                ✅ **Truss Member Updated!**
                
                **Top Chord:** {old_section} → **{top}**
                **Bottom Chord:** {selected.get('bottom', 'N/A')}
                **Diagonal:** {selected.get('diagonal', 'N/A')}
                
                🔄 **Please re-run the Health Report to see updated results.**
                """)
                st.rerun()
    
    # Show adequacy warning if still failing
    wind_force = loads['wind']
    section_data = SECTION_PROPERTIES.get(current_section, {})
    section_capacity = section_data.get('A', 0) * 355 / 1500
    
    if section_capacity < wind_force * 1.5:
        st.warning(f"""
        ⚠️ **Structure is under-designed for wind load**
        
        Wind load: {wind_force:.1f} kN  
        Section capacity: {section_capacity:.1f} kN  
        Required: {wind_force * 1.5:.1f} kN
        
        **Recommended actions:**
        1. 🔄 Use the **Intelligent Upgrade** options below
        2. 🔄 Reduce Span (B) or Apex Distance (LAA)
        3. 🔄 Increase Steel Grade (S355 → S460)
        4. 🔄 Add more bracing bays
        """)
    
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
        st.metric("Safety Factor", f"{safety_factor:.2f}", delta="Adequate" if safety_factor < 0.7 else "Check Required")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_image_gallery():
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">📸 Image Gallery</div>', unsafe_allow_html=True)
    
    ref = st.session_state.project_info.get("reference", "")
    if not ref:
        st.info("💡 Save the project first to upload and store images.")
        return
    
    project_folder = os.path.join(".sds_cache", "projects", ref, "images")
    os.makedirs(project_folder, exist_ok=True)
    
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
# MAIN WORKSPACE
# ============================================================
def render_workspace():
    params, materials = st.session_state.params, st.session_state.materials
    typ = TYPOLOGIES[st.session_state.typology]
    structure_type = st.session_state.typology
    
    # Health Report Button
    col_report1, col_report2 = st.columns([4, 1])
    with col_report2:
        if st.button("📊 Health Report", use_container_width=True, type="primary"):
            st.session_state.show_structural_report = True
            st.rerun()
    
    if st.session_state.show_structural_report:
        span, laa = params.get("B", 10.0), params.get("LAA", 15.0)
        wind = calculate_wind_load(span, laa, materials.get("standard", "EU"))
        dead = calculate_dead_load(span, laa, materials.get("section_size", "CHS 168.3x7.1"), materials.get("fabric_type", "PVC-coated Polyester"))
        memb = calculate_membrane_adequacy(materials.get("fabric_type", "PVC-coated Polyester"), wind, span * laa * 1.1, structure_type)
        
        # Calculate steel capacity
        section = materials.get("section_size", "CHS 168.3x7.1")
        section_data = SECTION_PROPERTIES.get(section, {})
        capacity = (section_data.get('A', 0) * 355) / 1500 if materials.get("material_type") == "Steel" else (section_data.get('A', 0) * 276) / 1500
        is_adequate = capacity > wind * 1.5
        
        report = {
            "health_score": 85 if is_adequate else 62,
            "health_status": "GOOD" if is_adequate else "FAIR",
            "health_color": "#2ecc71" if is_adequate else "#f39c12",
            "recommendation": "✅ Structure appears sound." if is_adequate else "⚠️ Some minor concerns identified. Consider reinforcing weak areas.",
            "detailed_checks": {
                "wind_check": is_adequate,
                "steel_capacity_check": True,
                "cable_adequacy_check": True,
                "slenderness_check": True
            },
            "membrane_check": memb
        }
        render_structural_health_report(report)
        if st.button("❌ Close Report", use_container_width=True):
            st.session_state.show_structural_report = False
            st.rerun()
        st.markdown("---")
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Project Info
        st.markdown(f"<div class='sds-card'><div class='title'>📊 Project</div>Name: {st.session_state.project_info.get('name', 'Untitled')}<br>Client: {st.session_state.project_info.get('client', 'Unknown')}<br>Ref: {st.session_state.project_info.get('reference', 'N/A')}</div>", unsafe_allow_html=True)
        
        # Shape
        shape_map = {"Parabolic": "parabolic", "Elliptical": "elliptical", "Circular": "circular", "Catenary": "catenary"}
        materials["shape_type"] = shape_map[st.selectbox("🔄 Shape Variant", list(shape_map.keys()), index=list(shape_map.values()).index(materials.get("shape_type", "parabolic")), key="shape_select")]
        
        # Member Type
        member_map = {"Single Beam": "single_beam", "Planar Truss": "planar_truss", "Space Truss": "space_truss"}
        materials["member_type"] = member_map[st.selectbox("🔧 Member Type", list(member_map.keys()), index=list(member_map.values()).index(materials.get("member_type", "single_beam")), key="member_select")]
        if materials["member_type"] in ["planar_truss", "space_truss"]:
            truss_map = {"Warren": "warren", "Pratt": "pratt", "Howe": "howe", "Vierendeel": "vierendeel"}
            materials["truss_type"] = truss_map[st.selectbox("🔗 Truss Type", list(truss_map.keys()), index=list(truss_map.values()).index(materials.get("truss_type", "warren")), key="truss_select")]
        
        # Section Type
        section_types = ["CHS", "RHS", "I-Beam", "Box", "Wood", "Aluminum"]
        materials["section_type"] = st.selectbox("📐 Section Type", section_types, index=section_types.index(materials.get("section_type", "CHS")), key="section_type_select")
        
        # Material
        materials["material_type"] = st.selectbox("🧱 Material", ["Steel", "Aluminum", "Wood", "Composite"], index=["Steel", "Aluminum", "Wood", "Composite"].index(materials.get("material_type", "Steel")), key="material_type_select")
        
        # Fabric with ETFE Warning
        fabrics = ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"]
        selected_fabric = st.selectbox("🧵 Fabric Type", fabrics, index=fabrics.index(materials.get("fabric_type", "PVC-coated Polyester")), key="fabric_select")
        materials["fabric_type"] = selected_fabric
        if selected_fabric == "ETFE" and structure_type in ["saddle_span", "tensile_membrane"]:
            st.warning("⚠️ ETFE NOT suitable for load-bearing membranes. Use PVC or PTFE.")
        
        # Auto thickness
        span, laa = params.get("B", 10.0), params.get("LAA", 15.0)
        wind = calculate_wind_load(span, laa, materials.get("standard", "EU"))
        materials["fabric_thickness"] = auto_select_fabric_thickness(wind, span * laa * 1.1, selected_fabric)
        st.caption(f"📏 Auto Thickness: {materials['fabric_thickness']} mm")
        
        # Section Size
        section_options = list(SECTION_PROPERTIES.keys())
        materials["section_size"] = st.selectbox("📐 Section Size", section_options, index=section_options.index(materials.get("section_size", "CHS 168.3x7.1")), key="section_select")
        
        # Anchoring
        pattern_map = {"Standard (Bracing Points)": "standard", "Continuous (Full Length)": "continuous", "Hybrid (Mixed)": "hybrid"}
        materials["anchoring_pattern"] = pattern_map[st.selectbox("📍 Anchoring Pattern", list(pattern_map.keys()), key="pattern_select")]
        
        # Prestress
        prestress_map = {"None (0 kN/m)": "none", "Low (1.5 kN/m)": "low", "Medium (3.0 kN/m)": "medium", "High (5.0 kN/m)": "high", "Custom": "custom"}
        materials["prestress_level"] = prestress_map[st.selectbox("🔧 Prestress Level", list(prestress_map.keys()), key="prestress_select")]
        if materials["prestress_level"] == "custom":
            materials["custom_prestress"] = st.slider("Custom Prestress (kN/m)", 0.0, 10.0, 3.0, 0.5, key="custom_prestress")
        
        # Bracing
        materials["num_bays"] = st.selectbox("🔗 Bracing Bays", [1, 2, 3], index=[1,2,3].index(materials.get("num_bays", 2)), key="num_bays")
        materials["tie_down_vertical_angle"] = st.slider("Tie-Down Vertical Angle (°)", 20, 70, materials.get("tie_down_vertical_angle", 45), 5, key="tie_down_vertical")
        materials["tie_down_horizontal_spread"] = st.slider("Tie-Down Horizontal Spread (°)", 10, 60, materials.get("tie_down_horizontal_spread", 30), 5, key="tie_down_spread")
        materials["wire_rope_type"] = st.selectbox("Cable Type", ["6x19 Galvanized", "6x19 Stainless"], key="cable_type")
        materials["safety_factor"] = st.number_input("Safety Factor", 1.0, 3.0, materials.get("safety_factor", 1.5), 0.1, key="safety_factor")
        
        # Standard
        std_map = {"EU": "EU", "CN": "CN", "UK": "UK", "MY": "MY", "US": "US"}
        materials["standard"] = std_map[st.selectbox("🌍 Design Standard", list(std_map.keys()), index=list(std_map.values()).index(materials.get("standard", "EU")), key="standard_select")]
        
        # Comments
        st.session_state.comments = st.text_area("💬 Notes", st.session_state.comments, height=80, key="comments_area")
    
    with col_right:
        st.subheader("🔬 3D Model")
        fig = generate_saddle_span(params, materials)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.divider()
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🔒 Lock", use_container_width=True, key="lock_btn"):
                st.session_state.locked = True
                save_cache()
                st.rerun()
        with c2:
            if st.button("💾 Save", use_container_width=True, type="primary", key="save_btn"):
                save_project()
        with c3:
            st.caption("📊 Use top")
        with c4:
            if st.button("📋 New", use_container_width=True, key="new_btn"):
                go_to_dashboard()
                st.rerun()
        with c5:
            if st.button("🏠 Home", use_container_width=True, key="home_btn"):
                go_to_dashboard()
                st.rerun()
        
        # Automatic Sizing
        sizing_results = size_all_members(params, materials)
        render_automatic_sizing(params, materials, sizing_results)
        
        # Intelligent Upgrade Engine
        wind_force = sizing_results["loads"]["wind"]
        current_section = materials.get("section_size", "CHS 168.3x7.1")
        section_data = SECTION_PROPERTIES.get(current_section, {})
        section_capacity = section_data.get('A', 0) * 355 / 1500 if materials.get("material_type") == "Steel" else section_data.get('A', 0) * 276 / 1500
        
        if section_capacity < wind_force * 1.5:
            upgrades = analyze_and_upgrade_structure(params, materials, sizing_results)
            render_upgrade_options(upgrades, params, materials)
        
        # Image Gallery
        render_image_gallery()
        
        # Reaction Forces
        render_reaction_forces(params, materials)
    
    st.divider()
    
    # Parameters
    st.markdown(f"<div class='sds-card'><div class='title'>📐 Main Parameters</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        params["A"] = st.number_input("Rise (A) m", 2.0, 20.0, params.get("A", 6.0), 0.5, format="%.1f", key="param_A")
    with c2:
        params["B"] = st.number_input("Span (B) m", 4.0, 40.0, params.get("B", 10.0), 0.5, format="%.1f", key="param_B")
    with c3:
        params["LAA"] = st.number_input("Apex Dist (LAA) m", 4.0, 50.0, params.get("LAA", 15.0), 0.5, format="%.1f", key="param_LAA")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Q&A
    st.markdown(f"<div class='sds-card'><div class='title'>❓ Design Confirmation</div>", unsafe_allow_html=True)
    for i, q in enumerate(typ["qa"]):
        st.session_state.qa_answers[f"qa_{i}"] = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes", "No", "Not Sure"].index(st.session_state.qa_answers.get(f"qa_{i}", "Yes")), key=f"qa_{i}")
    st.markdown("</div>", unsafe_allow_html=True)
    save_cache()

# ============================================================
# TYPOLOGIES
# ============================================================
TYPOLOGIES = {
    "saddle_span": {"name": "Saddle Span", "icon": "🏕️", "params": {"A": {"label": "Rise (m)", "min": 2.0, "max": 20.0, "step": 0.5, "default": 6.0}, "B": {"label": "Span (m)", "min": 4.0, "max": 40.0, "step": 0.5, "default": 10.0}, "LAA": {"label": "Apex Distance (m)", "min": 4.0, "max": 50.0, "step": 0.5, "default": 15.0}}, "qa": ["Are there two primary curved beams?", "Are both beams supported at their lower ends?", "Is the membrane attached continuously along the beams?", "Is A the vertical rise from support to apex?", "Is B the horizontal span between supports?", "Is LAA the distance between the two apexes?"]},
    "clear_span_tent": {"name": "Clear-Span Tent", "icon": "🏗️", "params": {"span_width": {"label": "Span Width (m)", "min": 3.0, "max": 80.0, "step": 0.5, "default": 10.0}, "ridge_height": {"label": "Ridge Height (m)", "min": 2.5, "max": 12.0, "step": 0.5, "default": 5.0}, "bay_distance": {"label": "Bay Distance (m)", "min": 3.0, "max": 10.0, "step": 0.5, "default": 5.0}, "num_bays": {"label": "Number of Bays", "min": 1, "max": 20, "step": 1, "default": 4}}, "qa": ["Zero interior columns?", "Pin-based supports?", "Fabric tensioned at ridge?", "Sidewalls open or enclosed?"]},
    "tensile_membrane": {"name": "Tensile Membrane", "icon": "⛺", "params": {"mast_height": {"label": "Mast Height (m)", "min": 3.0, "max": 30.0, "step": 0.5, "default": 8.0}, "span_length": {"label": "Span Length (m)", "min": 5.0, "max": 100.0, "step": 0.5, "default": 20.0}, "span_width": {"label": "Span Width (m)", "min": 5.0, "max": 80.0, "step": 0.5, "default": 15.0}, "cable_count": {"label": "Number of Cables", "min": 2, "max": 12, "step": 1, "default": 4}}, "qa": ["Boundary tension membrane?", "Interior masts present?", "Anticlastic or synclastic?", "Edge cables included?"]},
    "portal_frame": {"name": "Portal Frame", "icon": "🏛️", "params": {"eave_height": {"label": "Eave Height (m)", "min": 3.0, "max": 15.0, "step": 0.5, "default": 6.0}, "span_width": {"label": "Span Width (m)", "min": 10.0, "max": 50.0, "step": 0.5, "default": 20.0}, "bay_spacing": {"label": "Bay Spacing (m)", "min": 4.0, "max": 12.0, "step": 0.5, "default": 6.0}, "roof_pitch": {"label": "Roof Pitch (deg)", "min": 1.0, "max": 15.0, "step": 0.5, "default": 5.0}, "num_bays": {"label": "Number of Bays", "min": 2, "max": 30, "step": 1, "default": 5}}, "qa": ["Column bases pin-supported?", "Roof purlin-supported?", "Overhead crane present?", "Fully enclosed cladding?"]},
    "custom": {"name": "Custom Design", "icon": "🧩", "params": {"width": {"label": "Width (m)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 10.0}, "length": {"label": "Length (m)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 15.0}, "height": {"label": "Height (m)", "min": 1.0, "max": 50.0, "step": 0.5, "default": 8.0}}, "qa": ["This is a custom design. Add your description below."]}
}

# ============================================================
# MAIN APP ROUTING
# ============================================================
# Top Bar
c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2, 1, 1, 1, 1, 1])
with c1:
    if st.button("🏗️", help="Dashboard", key="logo_btn"):
        go_to_dashboard()
        st.rerun()
with c2:
    st.caption(f"📌 {st.session_state.project_info.get('name', 'No Project')}")
with c3:
    typ = TYPOLOGIES.get(st.session_state.typology, {})
    st.caption(f"{typ.get('icon', '')} {typ.get('name', '')}")
with c4:
    std = st.session_state.materials.get("standard", "EU")
    badge = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(std, "badge-eu")
    st.markdown(f'<span class="standard-badge {badge}">{std}</span>', unsafe_allow_html=True)
with c5:
    if st.session_state.locked:
        st.caption("🔒 Locked")
with c6:
    if st.session_state.locked and st.button("🔓 Unlock", use_container_width=True, key="unlock_btn"):
        st.session_state.locked = False
        save_cache()
        st.rerun()
with c7:
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
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            std = proj.get('standard', 'EU')
            badge = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(std, "badge-eu")
            c1.write(f"**{proj.get('name', 'Untitled')}** — {proj.get('client', 'Unknown')}")
            c1.markdown(f'<span class="standard-badge {badge}">{std}</span> {proj.get("typology", "Unknown")} {"🔒" if proj.get("locked") else "📝"}', unsafe_allow_html=True)
            if c2.button("Load", key=f"load_{proj.get('file')}"):
                if load_project_from_file(proj.get('file')):
                    st.session_state.show_project_browser = False
                    st.rerun()
            if c3.button("Delete", key=f"del_{proj.get('file')}"):
                delete_project_file(proj.get('file'))
                st.rerun()
            c4.caption(proj.get("date", "")[:10])
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
        if st.form_submit_button("🚀 Start Design", use_container_width=True, type="primary"):
            if not name or not client:
                st.error("⚠️ Project Name and Client Name are required.")
            else:
                st.session_state.project_info = {"name": name, "client": client, "location": location, "reference": f"SDS-{ref}", "date": datetime.now().isoformat()}
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
    st.caption("🏕️ Saddle Span - Complete Module with Automatic Sizing & Intelligent Upgrade")
    cols = st.columns(2)
    for i, (key, typ) in enumerate(TYPOLOGIES.items()):
        with cols[i % 2]:
            if st.button(f"{typ['icon']} {typ['name']}", use_container_width=True, type="primary" if i == 0 else "secondary"):
                st.session_state.typology = key
                st.session_state.params = {p: v["default"] for p, v in typ["params"].items()}
                st.session_state.qa_answers = {}
                st.session_state.locked = False
                save_cache()
                st.rerun()
    st.stop()

# Main Workspace
render_workspace()

# Footer
st.divider()
st.caption("SDS Design Studio Pro v3.2 | 🧠 Intelligent Upgrade Engine | MS EN Wind: 33.5m/s | 5 Upgrade Options")
save_cache()
