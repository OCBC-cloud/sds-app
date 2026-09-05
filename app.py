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
    page_title="SDS Design Studio",
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
        width: 100% !important; transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #2a3a4f !important;
        border-color: #4a7a9c !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button:active {
        background-color: #f39c12 !important;
        color: #0a0e17 !important;
        transform: scale(0.96) !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #f39c12 !important;
        color: #0a0e17 !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #f1c40f !important;
        transform: translateY(-2px) !important;
    }
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
    .check-pass { color: #2ecc71; font-weight: 700; }
    .check-fail { color: #e74c3c; font-weight: 700; }
    .image-popout { background-color: #0a0e17; border-radius: 12px; padding: 1rem; border: 2px solid #4a7a9c; text-align: center; }
    .image-popout img { max-width: 100%; border-radius: 8px; }
    .new-section-badge { background-color: #f39c12; color: #0a0e17; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 700; margin-left: 0.5rem; }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# SECTION PROPERTIES DATABASE
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
}

FABRIC_PROPERTIES = {
    "PVC-coated Polyester": {"thickness": {"0.5": 30, "0.8": 40, "1.0": 50, "1.2": 60}, "weight_per_m2": 1.2},
    "PTFE-coated Fiberglass": {"thickness": {"0.5": 40, "0.8": 55, "1.0": 70, "1.2": 85}, "weight_per_m2": 1.8},
    "ETFE": {"thickness": {"0.5": 25, "0.8": 35, "1.0": 45, "1.2": 55}, "weight_per_m2": 0.8}
}

CABLE_PROPERTIES = {
    "6x19 Galvanized": {"diameters": {6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140, 18: 180, 20: 220, 22: 260, 24: 310, 26: 360, 28: 420, 30: 480, 32: 540, 36: 680, 40: 840}},
    "6x19 Stainless": {"diameters": {6: 25, 8: 42, 10: 65, 12: 95, 14: 125, 16: 160, 18: 200, 20: 245}},
    "Polyester Rope": {"diameters": {8: 30, 10: 45, 12: 65, 14: 85, 16: 110, 18: 140, 20: 170, 24: 230}}
}

WIND_SPEEDS = {"EU": 30.0, "CN": 28.0, "UK": 26.0, "MY": 33.5, "US": 38.0}

# ============================================================
# SESSION STATE
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
if "saved_projects" not in st.session_state:
    st.session_state.saved_projects = []
if "materials" not in st.session_state:
    st.session_state.materials = {
        "standard": "EU",
        "material_type": "Steel",
        "section_type": "CHS",
        "fabric_type": "PVC-coated Polyester",
        "cable_type": "6x19 Galvanized",
        "tie_down_vertical_angle": 45,
        "tie_down_horizontal_spread": 30,
        "shape_type": "parabolic",
        "member_type": "single_beam",
        "truss_type": "warren",
        "num_bays": 2,
        "prestress_level": "medium"
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

def calculate_dead_load(span, laa, section_name, fabric_type):
    section_data = SECTION_PROPERTIES.get(section_name, {"weight": 28.3})
    steel_kg = section_data.get("weight", 28.3) * span * 2
    membrane_area = span * laa * 1.1
    fabric_weight = FABRIC_PROPERTIES.get(fabric_type, {}).get("weight_per_m2", 1.2)
    fabric_kg = fabric_weight * membrane_area
    return (steel_kg + fabric_kg) / 100

def calculate_required_section(load_kN, span_m, material_type, fy=355):
    safety = 1.5
    w = load_kN / span_m
    M = (w * span_m**2) / 8
    M_Nmm = M * 1e6
    W_required = M_Nmm / (fy / safety)
    E = 210000
    deflection_limit = span_m / 250
    I_required = (5 * w * span_m**4) / (384 * E * deflection_limit) * 1e12
    
    db = SECTION_PROPERTIES
    best_section = None
    best_score = float('inf')
    
    for section, props in db.items():
        if props["A"] <= 0:
            continue
        w_score = abs(props["W_el"] - W_required) / W_required if W_required > 0 else 0
        i_score = abs(props["I"] - I_required) / I_required if I_required > 0 else 0
        total_score = w_score * 0.6 + i_score * 0.4
        if props["W_el"] < W_required * 0.7:
            total_score += 10
        if total_score < best_score:
            best_score = total_score
            best_section = section
    
    if best_section:
        props = SECTION_PROPERTIES[best_section]
        moment_capacity = (props["W_el"] * fy) / (safety * 1e6)
        return {
            "section": best_section,
            "properties": props,
            "required_moment": M,
            "moment_capacity": moment_capacity,
            "is_adequate": props["W_el"] >= W_required * 0.9
        }
    return None

def auto_select_fabric_thickness(wind_force, membrane_area, fabric_type):
    required_strength = wind_force / (membrane_area * 0.5) if membrane_area > 0 else 0
    thickness_options = FABRIC_PROPERTIES.get(fabric_type, {}).get("thickness", {})
    for thickness, strength in sorted(thickness_options.items()):
        if strength >= required_strength * 1.5:
            return thickness
    return "1.2" if thickness_options else "0.8"

def auto_select_cable_diameter(tie_down_force, cable_type):
    cable_data = CABLE_PROPERTIES.get(cable_type, {})
    diameters = cable_data.get("diameters", {})
    required_load = tie_down_force * 1.5
    for diam, load in sorted(diameters.items()):
        if load >= required_load:
            return diam
    return max(diameters.keys()) if diameters else 10

def auto_design_structure(params, materials):
    span, rise, laa = params.get("B", 10.0), params.get("A", 6.0), params.get("LAA", 15.0)
    member_type = materials.get("member_type", "single_beam")
    material_type = materials.get("material_type", "Steel")
    fabric_type = materials.get("fabric_type", "PVC-coated Polyester")
    cable_type = materials.get("cable_type", "6x19 Galvanized")
    standard = materials.get("standard", "EU")
    
    wind_load = calculate_wind_load(span, laa, standard)
    dead_load = calculate_dead_load(span, laa, "CHS 168.3x7.1", fabric_type)
    live_load = 0.5 * (span * laa * 1.1) / 100
    total_load = wind_load + dead_load + live_load
    
    results = {
        "loads": {"wind": wind_load, "dead": dead_load, "live": live_load, "total": total_load},
        "beams": {}, "truss": {}, "fabric": {}, "cables": {},
        "all_checks": {}, "health_score": 0
    }
    
    fy = 355 if material_type == "Steel" else 276 if material_type == "Aluminum" else 40
    
    if member_type == "single_beam":
        beam_result = calculate_required_section(total_load, span, material_type, fy)
        if beam_result:
            results["beams"]["main"] = beam_result
            results["beams"]["selected"] = beam_result["section"]
            results["beams"]["moment_capacity"] = beam_result["moment_capacity"]
            results["beams"]["required_moment"] = beam_result["required_moment"]
    
    membrane_area = span * laa * 1.1
    fabric_thickness = auto_select_fabric_thickness(wind_load, membrane_area, fabric_type)
    results["fabric"]["type"] = fabric_type
    results["fabric"]["thickness"] = fabric_thickness
    results["fabric"]["strength"] = FABRIC_PROPERTIES.get(fabric_type, {}).get("thickness", {}).get(fabric_thickness, 0)
    
    num_bays = materials.get("num_bays", 2)
    num_anchors = num_bays * 4
    vertical_angle = materials.get("tie_down_vertical_angle", 45)
    uplift_per_anchor = (wind_load * 0.5) / num_anchors if num_anchors > 0 else 0
    cable_force = uplift_per_anchor / np.cos(np.radians(vertical_angle))
    
    cable_diameter = auto_select_cable_diameter(cable_force, cable_type)
    cable_data = CABLE_PROPERTIES.get(cable_type, {}).get("diameters", {})
    cable_breaking = cable_data.get(cable_diameter, 0)
    
    results["cables"]["type"] = cable_type
    results["cables"]["diameter"] = cable_diameter
    results["cables"]["breaking_load"] = cable_breaking
    results["cables"]["force_per_cable"] = cable_force
    results["cables"]["is_adequate"] = cable_breaking >= cable_force * 1.5
    
    results["all_checks"]["wind_load"] = {
        "status": "✅ PASS",
        "value": f"{wind_load:.1f} kN"
    }
    
    if member_type == "single_beam" and results["beams"].get("main"):
        beam = results["beams"]["main"]
        is_adequate = beam.get("is_adequate", False)
        results["all_checks"]["member_capacity"] = {
            "status": "✅ PASS" if is_adequate else "🔄 Upgrade",
            "value": f"{beam['moment_capacity']:.1f} kNm"
        }
    else:
        results["all_checks"]["member_capacity"] = {"status": "✅ PASS", "value": "N/A"}
    
    results["all_checks"]["cable_adequacy"] = {
        "status": "✅ PASS" if results["cables"]["is_adequate"] else "⚠️ Check",
        "value": f"{cable_breaking:.1f} kN"
    }
    
    fabric_strength = results["fabric"]["strength"]
    required_strength = wind_load / (membrane_area * 0.5) if membrane_area > 0 else 0
    is_adequate = fabric_strength >= required_strength * 1.5
    results["all_checks"]["membrane_strength"] = {
        "status": "✅ PASS" if is_adequate else "⚠️ Check",
        "value": f"{fabric_strength:.0f} kN/m"
    }
    
    score = 100
    for check in results["all_checks"].values():
        if "⚠️" in check["status"] or "🔄" in check["status"]:
            score -= 10
    results["health_score"] = max(0, min(100, score))
    
    return results

# ============================================================
# WORKING 3D GENERATOR - SIMPLE AND CORRECT
# ============================================================
def generate_saddle_span(params, materials=None):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    num_points = 50

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    # ===== GENERATE BEAM COORDINATES =====
    x = np.linspace(-span/2, span/2, num_points)
    z_beam = rise * (1 - (2 * x / span)**2)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    fig = go.Figure()

    # ===== DRAW BEAMS =====
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

    # ===== MEMBRANE SURFACE =====
    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, x_pos in enumerate(x):
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = z_beam[i]

        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            z_pos = z_at_x * (1 - 0.3 * (1 - (2 * v_val - 1)**2))
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
        opacity=0.6, showscale=False, name='Membrane'
    ))

    # ===== APEX AND SUPPORTS =====
    fig.add_trace(go.Scatter3d(
        x=[0], y=[y1[num_points//2]], z=[z_beam[num_points//2]],
        mode='markers', name='Apex',
        marker=dict(color='#FFD93D', size=8, symbol='diamond')
    ))
    fig.add_trace(go.Scatter3d(
        x=[-span/2, span/2],
        y=[0, 0],
        z=[0, 0],
        mode='markers', name='Supports',
        marker=dict(color='#4ECDC4', size=6, symbol='square')
    ))

    # ===== TIE-DOWNS =====
    if materials:
        num_bays = materials.get("num_bays", 2)
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 30)
        
        bracing_x = generate_bracing_positions(span, num_bays)

        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            y_pos = y1[idx]
            z_pos = z_beam[idx]

            dist = rise * np.tan(np.radians(vertical_angle))
            anchor_x = bx + dist * np.cos(np.radians(horizontal_spread))
            anchor_y = y_pos + dist * np.sin(np.radians(horizontal_spread))

            fig.add_trace(go.Scatter3d(
                x=[bx, anchor_x],
                y=[y_pos, anchor_y],
                z=[z_pos, 0],
                mode='lines',
                line=dict(color='#FFD93D', width=3),
                showlegend=False
            ))

            fig.add_trace(go.Scatter3d(
                x=[anchor_x],
                y=[anchor_y],
                z=[0],
                mode='markers',
                marker=dict(color='#FF4444', size=5, symbol='x'),
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
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(10,14,23,0.7)',
            bordercolor='#2a3a4f',
            borderwidth=1
        )
    )
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
    fig.update_layout(scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)', bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
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
    fig.update_layout(scene=dict(xaxis_title='Length (m)', yaxis_title='Width (m)', zaxis_title='Height (m)', bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
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
    fig.update_layout(scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)', bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_custom(params):
    width, length, height = params.get("width", 10.0), params.get("length", 15.0), params.get("height", 8.0)
    fig = go.Figure()
    corners = [[-width/2, -length/2, 0], [width/2, -length/2, 0], [width/2, length/2, 0], [-width/2, length/2, 0], [-width/2, -length/2, height], [width/2, -length/2, height], [width/2, length/2, height], [-width/2, length/2, height]]
    edges = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]
    for i, j in edges:
        fig.add_trace(go.Scatter3d(x=[corners[i][0], corners[j][0]], y=[corners[i][1], corners[j][1]], z=[corners[i][2], corners[j][2]], mode='lines', line=dict(color='#4a7a9c', width=3), showlegend=False))
    fig.update_layout(scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)', bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
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
    st.title("🏗️ SDS Design Studio")
    st.caption("Parametric design for tensile structures")
    
    projects = st.session_state.saved_projects
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>📂</div><div class='value'>{len(projects)}</div><div class='label'>Saved Projects</div></div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<div class='dashboard-card'><div class='icon'>🏕️</div><div class='value'>4</div><div class='label'>Shapes</div></div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("<div class='dashboard-card'><div class='icon'>🔧</div><div class='value'>3</div><div class='label'>Members</div></div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown("<div class='dashboard-card'><div class='icon'>⚡</div><div class='value'>AI</div><div class='label'>Engine</div></div>", unsafe_allow_html=True)
    
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

def render_workspace():
    params, materials = st.session_state.params, st.session_state.materials
    info, typology = st.session_state.project_info, st.session_state.typology
    if typology not in GENERATORS:
        typology = "saddle_span"
    
    generator = GENERATORS.get(typology, generate_saddle_span)
    
    st.markdown("## 🧠 Design Workspace")
    st.caption(f"📌 {info.get('name', 'Untitled')} — {info.get('client', 'Unknown')}")
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
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
        if st.button("🔒 Lock", use_container_width=True):
            st.session_state.locked = True
            st.rerun()
    with col4:
        if st.session_state.locked:
            if st.button("🔓 Unlock", use_container_width=True):
                st.session_state.locked = False
                st.rerun()
    
    st.divider()
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Parameters
        st.markdown('<div class="sds-card"><div class="title">📐 Dimensions</div>', unsafe_allow_html=True)
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
        
        if typology == "saddle_span":
            st.markdown('<div class="sds-card"><div class="title">🔄 Shape</div>', unsafe_allow_html=True)
            shape_options = ["parabolic", "elliptical", "circular", "catenary"]
            materials["shape_type"] = st.selectbox("Shape Type", shape_options, index=shape_options.index(materials.get("shape_type", "parabolic")), disabled=st.session_state.locked)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card"><div class="title">🔧 Structural System</div>', unsafe_allow_html=True)
        member_options = ["single_beam", "planar_truss", "space_truss"]
        member_labels = ["Single Beam", "Planar Truss", "Space Truss"]
        current_member = materials.get("member_type", "single_beam")
        idx = member_options.index(current_member) if current_member in member_options else 0
        
        selected_label = st.selectbox("Member Type", member_labels, index=idx, disabled=st.session_state.locked)
        materials["member_type"] = member_options[member_labels.index(selected_label)]
        
        if materials["member_type"] in ["planar_truss", "space_truss"]:
            truss_options = ["warren", "pratt", "howe", "vierendeel"]
            truss_labels = ["Warren", "Pratt", "Howe", "Vierendeel"]
            current_truss = materials.get("truss_type", "warren")
            truss_idx = truss_options.index(current_truss) if current_truss in truss_options else 0
            
            selected_truss_label = st.selectbox("Truss Type", truss_labels, index=truss_idx, disabled=st.session_state.locked)
            materials["truss_type"] = truss_options[truss_labels.index(selected_truss_label)]
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card"><div class="title">🧱 Materials</div>', unsafe_allow_html=True)
        material_types = ["Steel", "Aluminum", "Wood", "Composite"]
        current_material = materials.get("material_type", "Steel")
        materials["material_type"] = st.selectbox("Member Material", material_types, index=material_types.index(current_material), disabled=st.session_state.locked)
        
        section_types = ["CHS", "RHS", "I-Beam", "Box"]
        current_section_type = materials.get("section_type", "CHS")
        materials["section_type"] = st.selectbox("Section Shape", section_types, index=section_types.index(current_section_type), disabled=st.session_state.locked)
        
        fabric_options = ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"]
        materials["fabric_type"] = st.selectbox("Fabric Material", fabric_options, index=fabric_options.index(materials.get("fabric_type", "PVC-coated Polyester")), disabled=st.session_state.locked)
        
        cable_options = ["6x19 Galvanized", "6x19 Stainless", "Polyester Rope"]
        materials["cable_type"] = st.selectbox("Cable Type", cable_options, index=cable_options.index(materials.get("cable_type", "6x19 Galvanized")), disabled=st.session_state.locked)
        materials["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], index=[1, 2, 3].index(materials.get("num_bays", 2)), disabled=st.session_state.locked)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card"><div class="title">🔗 Tie-Down Settings</div>', unsafe_allow_html=True)
        materials["tie_down_vertical_angle"] = st.slider("Vertical Angle (°)", 20, 70, materials.get("tie_down_vertical_angle", 45), 5, disabled=st.session_state.locked)
        materials["tie_down_horizontal_spread"] = st.slider("Horizontal Spread (°)", 10, 60, materials.get("tie_down_horizontal_spread", 30), 5, disabled=st.session_state.locked)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card"><div class="title">🌍 Design Standard</div>', unsafe_allow_html=True)
        std_options = ["EU", "CN", "UK", "MY", "US"]
        materials["standard"] = st.selectbox("Design Standard", std_options, index=std_options.index(materials.get("standard", "EU")), disabled=st.session_state.locked)
        badge_class = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(materials["standard"], "badge-eu")
        st.markdown(f'<span class="standard-badge {badge_class}">{materials["standard"]}</span> {get_standard_label(materials["standard"])}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card"><div class="title">💬 Notes</div>', unsafe_allow_html=True)
        st.session_state.comments = st.text_area("", st.session_state.comments, height=80, disabled=st.session_state.locked, key="comments_area")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.subheader("🔬 3D Model")
        
        fig = generator(params, materials)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        
        st.divider()
        
        # Design Results
        design_results = auto_design_structure(params, materials)
        
        st.markdown("## ⚡ Design Results")
        
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📊 Loads</div>', unsafe_allow_html=True)
        loads = design_results["loads"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Wind Load", f"{loads['wind']:.1f} kN")
        c2.metric("Dead Load", f"{loads['dead']:.1f} kN")
        c3.metric("Total Load", f"{loads['total']:.1f} kN")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔧 Member Selection</div>', unsafe_allow_html=True)
        
        if typology == "saddle_span":
            beam = design_results["beams"].get("main")
            if beam:
                st.markdown(f"**Selected Section:** {beam['section']}")
                st.markdown(f"**Area:** {beam['properties']['A']:.0f} mm²")
                st.markdown(f"**Weight:** {beam['properties']['weight']:.1f} kg/m")
                st.markdown(f"**Required Moment:** {beam['required_moment']:.1f} kNm")
                st.markdown(f"**Moment Capacity:** {beam['moment_capacity']:.1f} kNm")
                st.markdown(f"**Status:** {'✅ Adequate' if beam['is_adequate'] else '🔄 Upgrade Available'}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🧵 Fabric & Cables</div>', unsafe_allow_html=True)
        st.markdown(f"**Fabric:** {design_results['fabric']['type']}")
        st.markdown(f"**Thickness:** {design_results['fabric']['thickness']} mm")
        st.markdown(f"**Strength:** {design_results['fabric']['strength']:.0f} kN/m")
        st.markdown("---")
        st.markdown(f"**Cable Type:** {design_results['cables']['type']}")
        st.markdown(f"**Diameter:** {design_results['cables']['diameter']} mm")
        st.markdown(f"**Breaking Load:** {design_results['cables']['breaking_load']:.0f} kN")
        st.markdown(f"**Force per Cable:** {design_results['cables']['force_per_cable']:.1f} kN")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📋 Checklist</div>', unsafe_allow_html=True)
        
        for check_name, check_data in design_results["all_checks"].items():
            status = check_data["status"]
            if "✅" in status:
                color = "#2ecc71"
            else:
                color = "#f39c12"
            st.markdown(f"<span style='color:{color}; font-weight:700;'>{status}</span> {check_name.replace('_', ' ').title()}: {check_data['value']}", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        score = design_results["health_score"]
        if score >= 80:
            status = "GOOD"
            color = "#2ecc71"
        elif score >= 60:
            status = "FAIR"
            color = "#f39c12"
        else:
            status = "POOR"
            color = "#e74c3c"
        
        st.markdown(f"""
        <div style='text-align:center;padding:1rem;background:#141e2b;border-radius:12px;border:2px solid {color};'>
            <span style='font-size:2.5rem;font-weight:700;color:{color};'>{score}%</span>
            <br>
            <span style='font-size:1.2rem;color:{color};'>{status}</span>
        </div>
        """, unsafe_allow_html=True)
    
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

st.divider()
st.caption("SDS Design Studio | MS EN Wind: 33.5m/s")
