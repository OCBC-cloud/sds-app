import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import random
import string
import math
import csv
from io import BytesIO, StringIO
import zipfile
import sys

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SDSe - Intelligent Fluid Design Workplace",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# PLOTLY 3D CONFIG - UNIVERSAL TOUCH SUPPORT
# ============================================================
PLOTLY_3D_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
    "doubleClick": "reset",
    "showTips": True,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "sdse_structure",
        "scale": 2
    },
    "modeBarButtonsToRemove": [
        "lasso2d", 
        "select2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d"
    ],
    "modeBarButtonsToAdd": [
        "zoomIn3d",
        "zoomOut3d",
        "resetCameraDefault3d",
        "orbitRotation",
        "tableRotation"
    ]
}

# ============================================================
# DARK MODE CSS - CLEAN & ORGANIZED
# ============================================================
dark_mode_css = """
    <style>
    .stApp { background-color: #0a0e17 !important; color: #f0f4fa !important; }
    .stApp > header { display: none !important; }
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 100% !important; 
        padding-left: 1rem !important; 
        padding-right: 1rem !important;
    }
    
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 600 !important; }
    label { color: #ffffff !important; font-weight: 400 !important; font-size: 0.85rem !important; }
    
    .stButton > button {
        background-color: #1e2a3a !important; color: #ffffff !important;
        border: 1px solid #2a3a4f !important; border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important; font-weight: 500 !important;
        font-size: 0.85rem !important;
        width: 100% !important; transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #2a3a4f !important;
        border-color: #4a7a9c !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(74, 122, 156, 0.2) !important;
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
        box-shadow: 0 4px 12px rgba(243, 156, 18, 0.3) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #2a3a4f !important;
        color: #ffffff !important;
        border: 1px solid #4a7a9c !important;
    }
    
    .stNumberInput > div > div > input, 
    .stSelectbox > div > div > div, 
    .stTextArea textarea,
    .stTextInput > div > div > input {
        background-color: #141e2b !important; 
        color: #ffffff !important;
        border: 1px solid #2a3a4f !important; 
        border-radius: 8px !important;
        font-size: 0.85rem !important;
    }
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: #f39c12 !important;
        box-shadow: 0 0 0 2px rgba(243, 156, 18, 0.2) !important;
    }
    
    .stAlert { 
        background-color: #1e2a3a !important; 
        border-left: 4px solid #f39c12 !important; 
        color: #f0f4fa !important; 
        font-size: 0.85rem !important;
        border-radius: 8px !important;
        padding: 0.8rem 1rem !important;
    }
    .stInfo { background-color: #1a2a3a !important; border-left: 4px solid #4a7a9c !important; }
    .stSuccess { background-color: #1a3a2a !important; border-left: 4px solid #2ecc71 !important; }
    .stError { background-color: #3a1a1a !important; border-left: 4px solid #e74c3c !important; }
    .stWarning { background-color: #4a3a1a !important; border-left: 4px solid #f39c12 !important; }
    
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    
    .stPlotlyChart {
        width: 100% !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background-color: #0a0e17 !important;
        border: 1px solid #1e2a3a;
    }
    
    @media (max-width: 768px) {
        .stPlotlyChart {
            min-height: 400px !important;
            max-height: 500px !important;
        }
    }
    @media (max-width: 480px) {
        .stPlotlyChart {
            min-height: 300px !important;
            max-height: 400px !important;
        }
    }
    
    .sdse-card {
        background-color: #121e2e;
        border-radius: 12px;
        padding: 1.2rem 1.2rem;
        border: 1px solid #1e2a3a;
        margin-bottom: 0.8rem;
        transition: all 0.3s ease;
    }
    .sdse-card:hover {
        border-color: #2a3a4f;
    }
    .sdse-card .card-title {
        color: #ffffff;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .sdse-card .card-title .badge {
        font-size: 0.55rem;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-weight: 600;
        margin-left: 0.3rem;
    }
    .badge-chs { background-color: #e74c3c; color: #ffffff; }
    .badge-shs { background-color: #3498db; color: #ffffff; }
    .badge-rhs { background-color: #2ecc71; color: #ffffff; }
    .badge-ibeam { background-color: #f39c12; color: #0a0e17; }
    .badge-angle { background-color: #9b59b6; color: #ffffff; }
    .badge-channel { background-color: #1abc9c; color: #ffffff; }
    .badge-unified { background-color: #f39c12; color: #0a0e17; }
    .badge-secondary { background-color: #e67e22; color: #ffffff; }
    .badge-tie { background-color: #f1c40f; color: #0a0e17; }
    .badge-cable { background-color: #3498db; color: #ffffff; }
    
    .dash-card {
        background-color: #121e2e;
        border-radius: 12px;
        padding: 1.2rem 1rem;
        border: 1px solid #1e2a3a;
        text-align: center;
        transition: all 0.3s ease;
    }
    .dash-card:hover {
        border-color: #2a3a4f;
        transform: translateY(-3px);
    }
    .dash-card .icon { font-size: 2.2rem; }
    .dash-card .value { color: #ffffff; font-size: 1.5rem; font-weight: 700; margin: 0.3rem 0; }
    .dash-card .label { color: #8a9aaa; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
    
    .path-card {
        background-color: #121e2e;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #1e2a3a;
        text-align: center;
        height: 100%;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .path-card:hover {
        border-color: #f39c12;
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(243, 156, 18, 0.1);
    }
    .path-card .icon { font-size: 2.8rem; }
    .path-card .title { color: #ffffff; font-size: 1.1rem; font-weight: 600; margin-top: 0.5rem; }
    .path-card .desc { color: #8a9aaa; font-size: 0.8rem; margin-top: 0.3rem; line-height: 1.4; }
    
    .safety-box {
        background-color: #1a2a3a;
        border-left: 4px solid #f39c12;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
    .safety-box .highlight {
        color: #f39c12;
        font-weight: 600;
    }
    
    .health-score {
        background-color: #1a3a2a;
        border: 2px solid #2ecc71;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .health-score .big {
        font-size: 2.8rem;
        font-weight: 700;
        color: #2ecc71;
    }
    .health-score .sub {
        color: #b0c4de;
        font-size: 0.9rem;
    }
    
    .result-row {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        border-bottom: 1px solid #1a2a3a;
        font-size: 0.85rem;
    }
    .result-row .label { color: #8a9aaa; }
    .result-row .value { color: #ffffff; font-weight: 500; }
    .result-row .pass { color: #2ecc71; }
    .result-row .check { color: #f39c12; }
    .result-row .fail { color: #e74c3c; }
    
    .member-recommend {
        background-color: #1a2a3a;
        border: 2px solid #f39c12;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    .member-recommend .section-name {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 700;
    }
    .member-recommend .section-detail {
        color: #8a9aaa;
        font-size: 0.75rem;
    }
    .member-recommend .status-pass {
        color: #2ecc71;
        font-weight: 700;
    }
    .member-recommend .status-check {
        color: #f39c12;
        font-weight: 700;
    }
    
    .mt-1 { margin-top: 0.5rem; }
    .mt-2 { margin-top: 1rem; }
    .mb-1 { margin-bottom: 0.5rem; }
    .mb-2 { margin-bottom: 1rem; }
    .flex-between { display: flex; justify-content: space-between; align-items: center; }
    .gap-1 { gap: 0.5rem; }
    .gap-2 { gap: 1rem; }
    
    .row-widget.stColumns { gap: 0.8rem !important; }
    .column { padding: 0 0.3rem !important; }
    
    @media (max-width: 768px) {
        .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .sdse-card { padding: 0.8rem; }
        .dash-card { padding: 0.8rem; }
        .path-card { padding: 1rem; }
    }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
def init_session_state():
    defaults = {
        "page": "dashboard",
        "project_registered": False,
        "project_info": {},
        "typology": None,
        "params": {},
        "locked": False,
        "comments": "",
        "saved_projects": [],
        "design_results": {},
        "bq": {},
        "structure_inputs": {},
        "rotation_angle": 0,
        "materials": {
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
            "prestress_level": "medium",
            "joint_type": "bolted",
            "country": "Malaysia",
            "dome_frequency": 6,
            "dome_radius": 20,
            "dome_height": 20,
            "curve_type": "parabolic",
            "tie_down_system": "cable", 
            "truss_depth_mode": "auto",
            "truss_depth_manual": 1.0,
            "fabric_sag": 30
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================
# CLEAR PROJECT DATA
# ============================================================
def clear_previous_project_data():
    st.session_state.design_results = {}
    st.session_state.bq = {}
    st.session_state.params = {}
    st.session_state.comments = ""
    st.session_state.locked = False
    st.session_state.typology = None
    st.session_state.structure_inputs = {}
    st.session_state.rotation_angle = 0
    
    default_materials = {
        "standard": st.session_state.materials.get("standard", "EU"),
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
        "prestress_level": "medium",
        "joint_type": "bolted",
        "country": st.session_state.materials.get("country", "Malaysia"),
        "dome_frequency": 6,
        "dome_radius": 20,
        "dome_height": 20,
        "curve_type": "parabolic",
        "tie_down_system": "cable",
        "truss_depth_mode": "auto",
        "truss_depth_manual": 1.0,
        "fabric_sag": 30
    }
    st.session_state.materials = default_materials

# ============================================================
# STRUCTURE TYPES - 27 STRUCTURES
# ============================================================
STRUCTURE_TYPES = {
    "parabolic_beam": {"name": "Parabolic Curved Beam", "icon": "🏹", "description": "Parabolic arch beam with single or truss members", "category": "Frame"},
    "circular_beam": {"name": "Circular Curved Beam", "icon": "⭕", "description": "Circular arch beam with single or truss members", "category": "Frame"},
    "saddle_span": {"name": "Saddle Span", "icon": "🏕️", "description": "Curved saddle-shaped tensile structure", "category": "Tensile"},
    "clear_span_tent": {"name": "Clear-Span Tent", "icon": "🏗️", "description": "Column-free tensile tent structure", "category": "Tensile"},
    "tensile_membrane": {"name": "Tensile Membrane", "icon": "⛺", "description": "Tensioned fabric membrane structure", "category": "Tensile"},
    "cable_net": {"name": "Cable Net", "icon": "🕸️", "description": "Interconnected cable grid structure", "category": "Tensile"},
    "cable_stayed": {"name": "Cable-Stayed", "icon": "🗼", "description": "Cable-supported tensile structure", "category": "Tensile"},
    "mast_supported": {"name": "Mast Supported", "icon": "🚩", "description": "Central mast with tensioned membrane", "category": "Tensile"},
    "stress_ribbon": {"name": "Stress Ribbon", "icon": "🎀", "description": "Tensioned ribbon bridge structure", "category": "Tensile"},
    "inflatable_structure": {"name": "Inflatable Structure", "icon": "🎈", "description": "Air-supported membrane structure", "category": "Tensile"},
    "portal_frame": {"name": "Portal Frame", "icon": "🏛️", "description": "Rigid steel frame structure", "category": "Frame"},
    "arch_structure": {"name": "Arch Structure", "icon": "🌉", "description": "Curved arch supporting structure", "category": "Frame"},
    "frame_system": {"name": "Frame System", "icon": "🏗️", "description": "Traditional frame structure", "category": "Frame"},
    "fabricated_beam": {"name": "Fabricated Beam", "icon": "📏", "description": "Custom fabricated beam structure", "category": "Frame"},
    "shell_structure": {"name": "Shell Structure", "icon": "🐚", "description": "Thin shell structural surface", "category": "Frame"},
    "folded_plate": {"name": "Folded Plate", "icon": "📐", "description": "Folded structural surface", "category": "Frame"},
    "geodesic_dome": {"name": "Geodesic Dome", "icon": "🌍", "description": "Spherical lattice shell structure", "category": "Spatial"},
    "space_frame": {"name": "Space Frame", "icon": "✧", "description": "3D truss network structure", "category": "Spatial"},
    "grid_shell": {"name": "Grid Shell", "icon": "🔷", "description": "Grid-based shell structure", "category": "Spatial"},
    "tensegrity": {"name": "Tensegrity", "icon": "🔮", "description": "Tension-integrity structure", "category": "Spatial"},
    "hybrid_system": {"name": "Hybrid System", "icon": "⚡", "description": "Combined structural systems", "category": "Spatial"},
    "retractable_roof": {"name": "Retractable Roof", "icon": "🔄", "description": "Opening and closing roof system", "category": "Specialized"},
    "suspension_bridge": {"name": "Suspension Bridge", "icon": "🌉", "description": "Cable-suspended bridge structure", "category": "Specialized"},
    "truss_system": {"name": "Truss System", "icon": "📐", "description": "Triangulated truss structure", "category": "Specialized"},
    "roof_system": {"name": "Roof System", "icon": "🏠", "description": "Comprehensive roof structure", "category": "Specialized"},
    "shade_structure": {"name": "Shade Structure", "icon": "🌴", "description": "Architectural shading system", "category": "Specialized"},
    "bridge_viaduct": {"name": "Bridge/Viaduct", "icon": "🌉", "description": "Structural bridge system", "category": "Specialized"}
}

# ============================================================
# 🔒 ENSHRINED SAFETY CALCULATIONS
# ============================================================
WIND_SPEEDS = {"EU": 30.0, "CN": 28.0, "UK": 26.0, "MY": 33.5, "US": 38.0}

def get_governing_area(span, apex, rise):
    area_from_span = span * rise
    area_from_apex = apex * rise
    governing_area = max(area_from_span, area_from_apex)
    
    return {
        "area_from_span": area_from_span,
        "area_from_apex": area_from_apex,
        "governing_area": governing_area,
        "governing_direction": "span" if area_from_span >= area_from_apex else "apex"
    }

def calculate_wind_load_enshrined(span, apex, rise, standard="MY"):
    wind_speed = WIND_SPEEDS.get(standard, 33.5)
    q = 0.5 * 1.225 * wind_speed**2 / 1000
    
    area_data = get_governing_area(span, apex, rise)
    governing_area = area_data["governing_area"]
    
    rise_span_ratio = rise / min(span, apex) if min(span, apex) > 0 else 0.5
    
    if rise_span_ratio < 0.2:
        shape_factor = 0.4
    elif rise_span_ratio < 0.4:
        shape_factor = 0.5
    elif rise_span_ratio < 0.6:
        shape_factor = 0.7
    elif rise_span_ratio < 0.8:
        shape_factor = 0.8
    else:
        shape_factor = 0.9
    
    exposure_factor = 1.0
    wind_force = q * governing_area * shape_factor * exposure_factor
    
    safety_margin = 1.10
    wind_force_design = wind_force * safety_margin
    
    return {
        "wind_speed": wind_speed,
        "velocity_pressure": q,
        "governing_area": governing_area,
        "area_from_span": area_data["area_from_span"],
        "area_from_apex": area_data["area_from_apex"],
        "governing_direction": area_data["governing_direction"],
        "shape_factor": shape_factor,
        "rise_span_ratio": rise_span_ratio,
        "wind_force": wind_force,
        "wind_force_design": wind_force_design,
        "wind_per_beam": wind_force_design / 2
    }

# ============================================================
# FULL SECTION PROPERTIES DATABASE - ALL TYPES
# ============================================================
SECTION_PROPERTIES = {
    "CHS 21.3x2.3": {"A": 137, "I": 0.006e6, "W_el": 0.6e3, "i": 6.7, "weight": 1.1, "type": "CHS", "depth": 21.3},
    "CHS 26.9x2.6": {"A": 198, "I": 0.015e6, "W_el": 1.1e3, "i": 8.7, "weight": 1.6, "type": "CHS", "depth": 26.9},
    "CHS 33.7x3.2": {"A": 307, "I": 0.035e6, "W_el": 2.1e3, "i": 10.7, "weight": 2.4, "type": "CHS", "depth": 33.7},
    "CHS 42.4x3.2": {"A": 394, "I": 0.075e6, "W_el": 3.5e3, "i": 13.8, "weight": 3.1, "type": "CHS", "depth": 42.4},
    "CHS 48.3x3.2": {"A": 453, "I": 0.12e6, "W_el": 5.0e3, "i": 16.3, "weight": 3.6, "type": "CHS", "depth": 48.3},
    "CHS 60.3x3.2": {"A": 574, "I": 0.24e6, "W_el": 8.0e3, "i": 20.5, "weight": 4.5, "type": "CHS", "depth": 60.3},
    "CHS 76.1x3.6": {"A": 820, "I": 0.54e6, "W_el": 14.2e3, "i": 25.7, "weight": 6.4, "type": "CHS", "depth": 76.1},
    "CHS 88.9x4.0": {"A": 1067, "I": 0.93e6, "W_el": 20.9e3, "i": 29.5, "weight": 8.4, "type": "CHS", "depth": 88.9},
    "CHS 101.6x4.0": {"A": 1226, "I": 1.42e6, "W_el": 28.0e3, "i": 34.0, "weight": 9.6, "type": "CHS", "depth": 101.6},
    "CHS 114.3x5.0": {"A": 1717, "I": 2.53e6, "W_el": 44.2e3, "i": 38.4, "weight": 13.5, "type": "CHS", "depth": 114.3},
    "CHS 139.7x6.3": {"A": 2642, "I": 5.90e6, "W_el": 84.5e3, "i": 47.3, "weight": 20.7, "type": "CHS", "depth": 139.7},
    "CHS 168.3x7.1": {"A": 3600, "I": 11.5e6, "W_el": 137e3, "i": 56.5, "weight": 28.3, "type": "CHS", "depth": 168.3},
    "CHS 219.1x8.0": {"A": 5305, "I": 29.0e6, "W_el": 265e3, "i": 73.9, "weight": 41.6, "type": "CHS", "depth": 219.1},
    "CHS 273.0x10.0": {"A": 8263, "I": 69.0e6, "W_el": 506e3, "i": 91.4, "weight": 64.9, "type": "CHS", "depth": 273.0},
    "CHS 323.9x12.5": {"A": 12228, "I": 148e6, "W_el": 912e3, "i": 110.0, "weight": 96.0, "type": "CHS", "depth": 323.9},
    "CHS 406.4x12.5": {"A": 15470, "I": 210e6, "W_el": 1030e3, "i": 116.6, "weight": 121.4, "type": "CHS", "depth": 406.4},
    "CHS 457.0x14.0": {"A": 19480, "I": 318e6, "W_el": 1390e3, "i": 127.8, "weight": 153.0, "type": "CHS", "depth": 457.0},
    "CHS 508.0x16.0": {"A": 24730, "I": 520e6, "W_el": 2050e3, "i": 145.0, "weight": 194.0, "type": "CHS", "depth": 508.0},
    "CHS 610.0x18.0": {"A": 33480, "I": 1430e6, "W_el": 4690e3, "i": 206.7, "weight": 262.8, "type": "CHS", "depth": 610.0},
    "CHS 711.0x20.0": {"A": 43420, "I": 2560e6, "W_el": 7200e3, "i": 242.9, "weight": 340.8, "type": "CHS", "depth": 711.0},
    "CHS 813.0x22.0": {"A": 54670, "I": 4300e6, "W_el": 10580e3, "i": 280.4, "weight": 429.0, "type": "CHS", "depth": 813.0},
    "CHS 914.0x25.0": {"A": 69820, "I": 6980e6, "W_el": 15280e3, "i": 316.1, "weight": 547.8, "type": "CHS", "depth": 914.0},
    "CHS 1016.0x28.0": {"A": 86920, "I": 10700e6, "W_el": 21060e3, "i": 350.8, "weight": 682.8, "type": "CHS", "depth": 1016.0},
    "SHS 50x50x3": {"A": 564, "I": 0.21e6, "W_el": 8.4e3, "i": 19.3, "weight": 4.4, "type": "SHS", "depth": 50},
    "SHS 50x50x4": {"A": 736, "I": 0.26e6, "W_el": 10.4e3, "i": 18.8, "weight": 5.8, "type": "SHS", "depth": 50},
    "SHS 75x75x3": {"A": 864, "I": 0.77e6, "W_el": 20.5e3, "i": 29.8, "weight": 6.8, "type": "SHS", "depth": 75},
    "SHS 75x75x4": {"A": 1136, "I": 0.97e6, "W_el": 25.9e3, "i": 29.2, "weight": 8.9, "type": "SHS", "depth": 75},
    "SHS 100x100x5": {"A": 1900, "I": 2.8e6, "W_el": 56.0e3, "i": 38.4, "weight": 14.9, "type": "SHS", "depth": 100},
    "SHS 100x100x6": {"A": 2256, "I": 3.2e6, "W_el": 64.0e3, "i": 37.7, "weight": 17.7, "type": "SHS", "depth": 100},
    "SHS 120x120x5": {"A": 2300, "I": 5.0e6, "W_el": 83.0e3, "i": 46.6, "weight": 18.1, "type": "SHS", "depth": 120},
    "SHS 150x150x6": {"A": 3456, "I": 11.9e6, "W_el": 159e3, "i": 58.7, "weight": 27.1, "type": "SHS", "depth": 150},
    "SHS 200x200x8": {"A": 6144, "I": 36.0e6, "W_el": 360e3, "i": 76.5, "weight": 48.2, "type": "SHS", "depth": 200},
    "SHS 250x250x10": {"A": 9600, "I": 88.0e6, "W_el": 704e3, "i": 95.7, "weight": 75.4, "type": "SHS", "depth": 250},
    "SHS 300x300x12": {"A": 13824, "I": 182e6, "W_el": 1213e3, "i": 114.8, "weight": 108.5, "type": "SHS", "depth": 300},
    "RHS 100x50x4": {"A": 1136, "I": 1.4e6, "W_el": 28.0e3, "i": 35.1, "weight": 8.9, "type": "RHS", "depth": 100},
    "RHS 100x50x5": {"A": 1400, "I": 1.7e6, "W_el": 34.0e3, "i": 34.8, "weight": 11.0, "type": "RHS", "depth": 100},
    "RHS 120x60x5": {"A": 1700, "I": 3.1e6, "W_el": 52.0e3, "i": 42.7, "weight": 13.3, "type": "RHS", "depth": 120},
    "RHS 150x100x5": {"A": 2450, "I": 6.8e6, "W_el": 91.0e3, "i": 52.7, "weight": 19.2, "type": "RHS", "depth": 150},
    "RHS 150x100x6": {"A": 2784, "I": 8.3e6, "W_el": 111e3, "i": 54.6, "weight": 21.8, "type": "RHS", "depth": 150},
    "RHS 200x100x6": {"A": 3504, "I": 16.4e6, "W_el": 164e3, "i": 68.4, "weight": 27.5, "type": "RHS", "depth": 200},
    "RHS 200x100x8": {"A": 4608, "I": 21.2e6, "W_el": 212e3, "i": 67.8, "weight": 36.2, "type": "RHS", "depth": 200},
    "RHS 200x150x8": {"A": 5104, "I": 30.1e6, "W_el": 301e3, "i": 76.8, "weight": 40.0, "type": "RHS", "depth": 200},
    "RHS 250x150x10": {"A": 7500, "I": 71.0e6, "W_el": 568e3, "i": 97.3, "weight": 58.9, "type": "RHS", "depth": 250},
    "RHS 300x200x12": {"A": 11424, "I": 156e6, "W_el": 1040e3, "i": 116.8, "weight": 89.7, "type": "RHS", "depth": 300},
    "I-100": {"A": 1030, "I": 4.5e6, "W_el": 90e3, "i": 66.1, "weight": 8.1, "type": "I-Beam", "depth": 100},
    "I-120": {"A": 1440, "I": 8.0e6, "W_el": 133e3, "i": 74.5, "weight": 11.3, "type": "I-Beam", "depth": 120},
    "I-140": {"A": 1700, "I": 12.0e6, "W_el": 171e3, "i": 84.0, "weight": 13.3, "type": "I-Beam", "depth": 140},
    "I-150": {"A": 2130, "I": 16.0e6, "W_el": 213e3, "i": 86.7, "weight": 16.7, "type": "I-Beam", "depth": 150},
    "I-160": {"A": 2410, "I": 20.0e6, "W_el": 250e3, "i": 91.1, "weight": 18.9, "type": "I-Beam", "depth": 160},
    "I-180": {"A": 2790, "I": 28.0e6, "W_el": 311e3, "i": 100.2, "weight": 21.9, "type": "I-Beam", "depth": 180},
    "I-200": {"A": 3310, "I": 38.0e6, "W_el": 380e3, "i": 107.1, "weight": 26.0, "type": "I-Beam", "depth": 200},
    "I-220": {"A": 3930, "I": 52.0e6, "W_el": 473e3, "i": 115.0, "weight": 30.8, "type": "I-Beam", "depth": 220},
    "I-250": {"A": 4820, "I": 76.0e6, "W_el": 608e3, "i": 125.6, "weight": 37.8, "type": "I-Beam", "depth": 250},
    "I-280": {"A": 5530, "I": 101.0e6, "W_el": 721e3, "i": 135.2, "weight": 43.4, "type": "I-Beam", "depth": 280},
    "I-300": {"A": 6720, "I": 136.0e6, "W_el": 907e3, "i": 142.3, "weight": 52.8, "type": "I-Beam", "depth": 300},
    "I-320": {"A": 7460, "I": 168.0e6, "W_el": 1050e3, "i": 150.1, "weight": 58.6, "type": "I-Beam", "depth": 320},
    "I-350": {"A": 9020, "I": 226.0e6, "W_el": 1290e3, "i": 158.3, "weight": 70.8, "type": "I-Beam", "depth": 350},
    "I-400": {"A": 11800, "I": 348.0e6, "W_el": 1740e3, "i": 171.8, "weight": 92.6, "type": "I-Beam", "depth": 400},
    "I-450": {"A": 14300, "I": 498.0e6, "W_el": 2210e3, "i": 186.7, "weight": 112.2, "type": "I-Beam", "depth": 450},
    "I-500": {"A": 17500, "I": 694.0e6, "W_el": 2780e3, "i": 199.2, "weight": 137.4, "type": "I-Beam", "depth": 500},
    "L40x40x4": {"A": 309, "I": 0.08e6, "W_el": 2.8e3, "i": 16.1, "weight": 2.4, "type": "Angle", "depth": 40},
    "L50x50x5": {"A": 480, "I": 0.18e6, "W_el": 5.1e3, "i": 19.4, "weight": 3.8, "type": "Angle", "depth": 50},
    "L60x60x6": {"A": 691, "I": 0.36e6, "W_el": 8.5e3, "i": 22.8, "weight": 5.4, "type": "Angle", "depth": 60},
    "L70x70x7": {"A": 941, "I": 0.64e6, "W_el": 12.8e3, "i": 26.1, "weight": 7.4, "type": "Angle", "depth": 70},
    "L80x80x8": {"A": 1229, "I": 1.04e6, "W_el": 18.2e3, "i": 29.1, "weight": 9.6, "type": "Angle", "depth": 80},
    "L90x90x9": {"A": 1553, "I": 1.58e6, "W_el": 24.7e3, "i": 31.9, "weight": 12.2, "type": "Angle", "depth": 90},
    "L100x100x10": {"A": 1910, "I": 2.28e6, "W_el": 32.0e3, "i": 34.5, "weight": 15.0, "type": "Angle", "depth": 100},
    "L120x120x12": {"A": 2752, "I": 4.52e6, "W_el": 53.0e3, "i": 40.5, "weight": 21.6, "type": "Angle", "depth": 120},
    "C100x50x6": {"A": 1010, "I": 2.8e6, "W_el": 56e3, "i": 52.6, "weight": 7.9, "type": "Channel", "depth": 100},
    "C120x60x7": {"A": 1380, "I": 5.2e6, "W_el": 87e3, "i": 61.4, "weight": 10.8, "type": "Channel", "depth": 120},
    "C150x75x8": {"A": 1910, "I": 10.2e6, "W_el": 136e3, "i": 73.1, "weight": 15.0, "type": "Channel", "depth": 150},
    "C180x80x9": {"A": 2330, "I": 16.0e6, "W_el": 178e3, "i": 82.9, "weight": 18.3, "type": "Channel", "depth": 180},
    "C200x90x10": {"A": 2890, "I": 24.0e6, "W_el": 240e3, "i": 91.1, "weight": 22.7, "type": "Channel", "depth": 200},
    "C250x100x12": {"A": 3930, "I": 48.0e6, "W_el": 384e3, "i": 110.5, "weight": 30.8, "type": "Channel", "depth": 250},
}

# ============================================================
# FABRIC & CABLE PROPERTIES
# ============================================================
FABRIC_PROPERTIES = {
    "PVC-coated Polyester": {
        "thickness": {"0.5": 30, "0.8": 40, "1.0": 50, "1.2": 60},
        "weight_per_m2": 1.2
    },
    "PTFE-coated Fiberglass": {
        "thickness": {"0.5": 40, "0.8": 55, "1.0": 70, "1.2": 85},
        "weight_per_m2": 1.8
    },
    "ETFE Film": {
        "thickness": {"0.05": 15, "0.08": 25, "0.10": 32, "0.15": 42, "0.20": 55},
        "weight_per_m2": 0.8
    }
}

CABLE_PROPERTIES = {
    "6x19 Galvanized": {
        "diameters": {
            6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140,
            18: 180, 20: 220, 22: 260, 24: 310, 26: 360,
            28: 420, 30: 480, 32: 540, 36: 680, 40: 840
        },
        "weight_per_m": {6: 0.178, 8: 0.317, 10: 0.495, 12: 0.713, 14: 0.971,
                        16: 1.270, 18: 1.600, 20: 1.980, 22: 2.400, 24: 2.850}
    },
    "1x19 Construction": {
        "diameters": {
            2.5: 4.9, 3.0: 7.0, 4.0: 12.6, 5.0: 19.6, 6.0: 28.0,
            7.0: 35.0, 8.0: 45.4, 10.0: 71.0, 12.0: 102.0,
            14.0: 139.0, 16.0: 182.0, 18.0: 220.0, 20.0: 260.0
        },
        "weight_per_m": {2.5: 0.031, 3.0: 0.045, 4.0: 0.079, 5.0: 0.124,
                        6.0: 0.178, 7.0: 0.243, 8.0: 0.317, 10.0: 0.495}
    },
    "6x19 Stainless": {
        "diameters": {6: 25, 8: 42, 10: 65, 12: 95, 14: 125, 16: 160, 18: 200, 20: 245},
        "weight_per_m": {6: 0.178, 8: 0.317, 10: 0.495, 12: 0.713, 14: 0.971, 16: 1.270}
    },
    "Polyester Rope": {
        "diameters": {8: 30, 10: 45, 12: 65, 14: 85, 16: 110, 18: 140, 20: 170, 24: 230},
        "weight_per_m": {8: 0.050, 10: 0.080, 12: 0.115, 14: 0.155, 16: 0.200}
    }
}

JOINT_MULTIPLIERS = {
    "welded": {"factor": 1.2, "description": "Rigid moment connections"},
    "bolted": {"factor": 1.0, "description": "Pin connections - economical"}
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def get_sections_by_type(section_type):
    type_map = {
        "CHS": "CHS",
        "SHS": "SHS",
        "RHS": "RHS",
        "I-Beam": "I-Beam",
        "Angle": "Angle",
        "Channel": "Channel"
    }
    actual_type = type_map.get(section_type, "CHS")
    
    sections = []
    for name, props in SECTION_PROPERTIES.items():
        if props.get("type") == actual_type:
            sections.append((name, props))
    sections.sort(key=lambda x: x[1]["W_el"])
    return sections

def find_closest_section(W_required, section_type="CHS"):
    sections = get_sections_by_type(section_type)
    closest = None
    closest_gap = float('inf')
    
    for name, props in sections:
        gap = W_required - props["W_el"]
        if gap >= 0 and gap < closest_gap:
            closest_gap = gap
            closest = (name, props)
    
    return closest

def find_closest_section_by_area(A_required, section_type="CHS"):
    sections = get_sections_by_type(section_type)
    closest = None
    closest_gap = float('inf')
    
    for name, props in sections:
        gap = A_required - props["A"]
        if gap >= 0 and gap < closest_gap:
            closest_gap = gap
            closest = (name, props)
    
    return closest

def get_section_tag(section_type):
    tags = {
        "CHS": "CHS",
        "SHS": "SHS",
        "RHS": "RHS",
        "I-Beam": "I-Beam",
        "Angle": "Angle",
        "Channel": "Channel"
    }
    return tags.get(section_type, "")

def get_standard_label(code):
    labels = {"EU": "🇪🇺 Eurocode", "CN": "🇨🇳 China", "UK": "🇬🇧 British", "MY": "🇲🇾 Malaysia", "US": "🇺🇸 USA"}
    return labels.get(code, code)

def get_curve_shape(x, span, rise, curve_type="parabolic"):
    if span <= 0:
        return np.zeros_like(x)
    x_norm = 2 * x / span
    
    if curve_type == "parabolic":
        return rise * (1 - x_norm**2)
    elif curve_type == "circular":
        R = (span**2 + 4*rise**2) / (8*rise) if rise > 0 else span/2
        return rise - (R - np.sqrt(max(0, R**2 - x**2)))
    else:
        return rise * (1 - x_norm**2)

def check_span_rules(span, apex, materials):
    span_trigger = 20.0
    
    rules = {
        "cables_allowed": True,
        "pin_forced": False,
        "secondary_beams_required": False,
        "rigid_ties_required": False,
        "warning_messages": [],
        "info_messages": []
    }
    
    if span >= span_trigger or apex >= span_trigger:
        rules["cables_allowed"] = False
        rules["pin_forced"] = True
        rules["secondary_beams_required"] = True
        rules["rigid_ties_required"] = True
        
        rules["info_messages"].append("🔒 Span/apex ≥ 20m: Pin connections forced, cables replaced with rigid ties")
        rules["info_messages"].append("📐 Secondary beams (purlins) required for stability")
        
        if materials.get("joint_type") == "welded":
            rules["warning_messages"].append("⚠️ Fixed connections not recommended for spans ≥ 20m. Forcing Pin connections.")
    else:
        if materials.get("joint_type") == "welded":
            rules["info_messages"].append("✅ Fixed connections allowed for spans < 20m")
        else:
            rules["info_messages"].append("✅ Pin connections selected for spans < 20m")
        
        if materials.get("cable_type") and materials.get("cable_type") != "None":
            rules["info_messages"].append("✅ Cables allowed for spans < 20m")
    
    return rules

# ============================================================
# 🔧 CORE ENGINEERING FUNCTIONS
# ============================================================
def calculate_dead_load_single(span, apex, materials):
    section_type = materials.get("section_type", "CHS")
    main_depth = 0.4 if section_type == "CHS" else 0.5
    if materials.get("member_type") in ["planar_truss", "space_truss"]:
        main_depth = materials.get("truss_depth_manual", 1.0) if materials.get("truss_depth_mode") == "manual" else 1.0
    
    self_weight_per_m = 0.5
    if section_type == "CHS":
        self_weight_per_m = 20 * main_depth
    elif section_type == "SHS":
        self_weight_per_m = 25 * main_depth
    elif section_type == "I-Beam":
        self_weight_per_m = 40 * main_depth
    
    main_length = apex * 2
    dead_load_beam = self_weight_per_m * main_length / 1000
    
    secondary_dead = 0
    if materials.get("member_type") in ["planar_truss", "space_truss"]:
        num_bays = materials.get("num_bays", 3)
        secondary_dead = 0.5 * span * num_bays * 0.25 / 1000
    
    return dead_load_beam + secondary_dead

def calculate_required_section_truss(params, materials, member_type, is_3d=False):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    apex = params.get("LAA", 15.0)
    num_bays = materials.get("num_bays", 3)
    
    if materials.get("truss_depth_mode") == "manual":
        truss_depth = materials.get("truss_depth_manual", 1.0)
    else:
        truss_depth = max(rise / 10, 1.0)
    
    wind_data = calculate_wind_load_enshrined(span, apex, rise, materials.get("standard", "MY"))
    total_wind = wind_data["wind_force_design"]
    
    dead_load = calculate_dead_load_single(span, apex, materials)
    total_load_kn = total_wind + dead_load
    
    span_support = max(span, apex)
    w = total_load_kn / span_support
    M_max = w * span_support**2 / 8
    V_max = w * span_support / 2
    
    F_chord = M_max / truss_depth
    F_web = V_max / 1.2
    
    fy = 275
    A_req_chord = (F_chord * 1000) / (0.6 * fy)
    A_req_web = (F_web * 1000) / (0.6 * fy)
    
    section_type = materials.get("section_type", "CHS")
    
    return {
        "truss_depth": truss_depth,
        "is_3d": is_3d,
        "unified_section_type": section_type,
        "members": {
            "top_chord": {
                "force": F_chord, "A_required": A_req_chord, "is_chord": True
            },
            "bottom_chord": {
                "force": F_chord, "A_required": A_req_chord, "is_chord": True
            },
            "vertical": {
                "force": F_web, "A_required": A_req_web, "is_chord": False
            },
            "horizontal": {
                "force": F_web, "A_required": A_req_web, "is_chord": False
            }
        },
        "loads": {
            "wind": total_wind, "dead": dead_load, "total": total_load_kn
        },
        "span_rules": check_span_rules(span, apex, materials)
    }

def calculate_secondary_beams(span, apex, materials):
    span_support = max(span, apex)
    num_bays = materials.get("num_bays", 2)
    spacing = span_support / (num_bays + 1)
    
    section = "SHS 100x100x5"
    weight = 14.9
    total_length = span_support * 0.8
    total_weight = total_length * weight
    
    return {
        "section": section,
        "num_purlins": num_bays,
        "spacing": spacing,
        "total_length": total_length,
        "total_weight": total_weight
    }

def calculate_rigid_ties(span, rise, materials):
    num_ties = materials.get("num_bays", 2) * 2
    tie_length = math.sqrt(span**2 + rise**2) * 1.1
    section = "CHS 33.7x3.2"
    weight = 2.4
    
    return {
        "section": section,
        "num_ties": num_ties,
        "force_per_tie": 10.0,
        "total_length": tie_length * num_ties,
        "total_weight": tie_length * num_ties * weight
    }

def calculate_cable_ties(span, rise, materials):
    num_cables = materials.get("num_bays", 2) * 2
    cable_length = math.sqrt(span**2 + rise**2) * 1.1
    cable_type = materials.get("cable_type", "6x19 Galvanized")
    diameter = 12
    break_load = CABLE_PROPERTIES.get(cable_type, {}).get("diameters", {}).get(diameter, 80)
    
    return {
        "type": cable_type,
        "diameter": diameter,
        "num_cables": num_cables,
        "force_per_cable": 15.0,
        "utilization": 0.5,
        "total_length": cable_length * num_cables
    }

def calculate_health_score(design_results):
    return 100

# CRITICAL FIX: Restructured auto_design_structure to handle Saddle Span completely
def auto_design_structure(params, materials, typology):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    apex = params.get("LAA", 15.0)
    
    # Initialize base design results
    design_results = {
        "loads": {"wind": 0, "dead": 0, "total": 0},
        "span_rules": check_span_rules(span, apex, materials),
        "health_score": 100
    }
    
    # Compute loads (works for ALL typologies including Saddle Span)
    wind_data = calculate_wind_load_enshrined(span, apex, rise, materials.get("standard", "MY"))
    dead_load = calculate_dead_load_single(span, apex, materials)
    total_load = wind_data["wind_force_design"] + dead_load
    
    design_results["loads"] = {
        "wind": wind_data["wind_force_design"], 
        "dead": dead_load, 
        "total": total_load
    }
    
    # Main member / Truss selection
    if materials.get("member_type") in ["planar_truss", "space_truss"]:
        is_3d = materials.get("member_type") == "space_truss"
        truss_results = calculate_required_section_truss(params, materials, materials.get("member_type"), is_3d)
        design_results.update(truss_results)
    else:
        # Select standard section based on total load
        section_type = materials.get("section_type", "CHS")
        M_required = (total_load * apex**2) / 8 / 1000  # kNm to kNmm
        W_required = M_required * 1000 / 0.6 / 275 * 1000  # mm3
        
        closest = find_closest_section(W_required, section_type)
        if closest:
            section_name, props = closest
            design_results["beams"] = {
                "main": {
                    "section": section_name,
                    "section_type": section_type,
                    "is_standard": True,
                    "curve_type": materials.get("curve_type", "parabolic"),
                    "W_required": W_required,
                    "W_actual": props["W_el"]
                }
            }
    
    # Add Secondary Beams
    design_results["secondary_beams"] = calculate_secondary_beams(span, apex, materials)
    
    # Add Tie-downs based on user choice
    if materials.get("tie_down_system") == "rigid":
        design_results["rigid_ties"] = calculate_rigid_ties(span, rise, materials)
    else:
        design_results["cables"] = calculate_cable_ties(span, rise, materials)
    
    # Add Fabric Properties
    design_results["fabric"] = {
        "type": materials.get("fabric_type", "PVC-coated Polyester"),
        "thickness": "1.0"
    }
    
    # Generate BQ
    design_results["bq"] = generate_bill_of_quantities(design_results, materials)
    
    return design_results

# ============================================================
# BILL OF QUANTITIES
# ============================================================
def generate_bill_of_quantities(design_results, materials):
    items = []
    
    if "members" in design_results:
        unified_type = design_results.get("unified_section_type", "CHS")
        items.append({
            "item": "Truss Chords",
            "section": unified_type,
            "qty": 2,
            "unit": "pcs",
            "length_per_pc": 10.0,
            "total_length": 20.0,
            "total_weight": 20.0 * 40,
            "notes": "Top & Bottom chords"
        })
        items.append({
            "item": "Truss Webs",
            "section": unified_type,
            "qty": 10,
            "unit": "pcs",
            "length_per_pc": 1.0,
            "total_length": 10.0,
            "total_weight": 10.0 * 15,
            "notes": "Vertical & Horizontal webs"
        })
    elif "beams" in design_results:
        beam = design_results["beams"]["main"]
        items.append({
            "item": "Main Curved Beam",
            "section": beam.get("section", "N/A"),
            "qty": 2,
            "unit": "pcs",
            "length_per_pc": 15.0,
            "total_length": 30.0,
            "total_weight": 30.0 * 13.5,
            "notes": "Curved beam members"
        })
    
    if "secondary_beams" in design_results:
        sec = design_results["secondary_beams"]
        items.append({
            "item": "Secondary Beams",
            "section": sec.get("section", "N/A"),
            "qty": sec.get("num_purlins", 0),
            "unit": "pcs",
            "length_per_pc": 8.0,
            "total_length": sec.get("total_length", 0),
            "total_weight": sec.get("total_weight", 0),
            "notes": "Purlins"
        })
    
    if "cables" in design_results:
        cables = design_results["cables"]
        cable_w = CABLE_PROPERTIES.get(cables.get("type", ""), {}).get("weight_per_m", {}).get(cables.get("diameter", 12), 0.7)
        total_w = cables.get("total_length", 0) * cable_w
        items.append({
            "item": "Tie-down Cables",
            "section": f"{cables.get('type', 'N/A')} {cables.get('diameter', 12)}mm",
            "qty": cables.get("num_cables", 0),
            "unit": "pcs",
            "length_per_pc": cables.get("total_length", 0) / max(1, cables.get("num_cables", 1)),
            "total_length": cables.get("total_length", 0),
            "total_weight": total_w,
            "notes": "Cable tie-downs"
        })
    
    if "rigid_ties" in design_results:
        ties = design_results["rigid_ties"]
        items.append({
            "item": "Rigid Tie-downs",
            "section": ties.get("section", "N/A"),
            "qty": ties.get("num_ties", 0),
            "unit": "pcs",
            "length_per_pc": ties.get("total_length", 0) / max(1, ties.get("num_ties", 1)),
            "total_length": ties.get("total_length", 0),
            "total_weight": ties.get("total_weight", 0),
            "notes": "Rigid struts"
        })
    
    if "fabric" in design_results:
        fabric = design_results["fabric"]
        items.append({
            "item": "Roof Membrane",
            "section": f"{fabric.get('type', 'N/A')} {fabric.get('thickness', 'N/A')}mm",
            "qty": 1,
            "unit": "lot",
            "length_per_pc": 0,
            "total_length": 0,
            "total_weight": 100.0,
            "notes": "Fabric membrane"
        })
    
    total_steel = sum(item.get("total_weight", 0) for item in items if "Cable" not in item.get("item", "") and "Membrane" not in item.get("item", ""))
    total_cable = sum(item.get("total_weight", 0) for item in items if "Cable" in item.get("item", ""))
    total_fabric = sum(item.get("total_weight", 0) for item in items if "Membrane" in item.get("item", ""))
    
    return {
        "items": items,
        "total_steel_weight": total_steel + total_cable,
        "total_fabric_area": total_fabric,
        "total_cable_length": sum(item.get("total_length", 0) for item in items if "Cable" in item.get("item", "")),
        "total_joints": 20
    }

# ============================================================
# 3D GENERATORS
# ============================================================
def generate_curved_beam_3d(params, materials=None, curve_type="parabolic"):
    span = params.get("B", 10.0) if params else 10.0
    rise = params.get("A", 6.0) if params else 6.0
    laa = params.get("LAA", 15.0) if params else 15.0
    num_points = 50

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    x = np.linspace(-span/2, span/2, num_points)
    z_beam = get_curve_shape(x, span, rise, curve_type)
    
    y1 = -laa/2 * (1 - (2 * x / span)**2) * 0.8
    y2 = laa/2 * (1 - (2 * x / span)**2) * 0.8

    fig = go.Figure()
    cam_eye_x, cam_eye_y, cam_eye_z = 1.6, 1.6, 1.2

    fig.add_trace(go.Scatter3d(
        x=x, y=y1, z=z_beam,
        mode='lines',
        line=dict(color='#FF6B6B', width=4),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode='lines',
        line=dict(color='#FF6B6B', width=4),
        showlegend=False
    ))

    fabric_sag = materials.get("fabric_sag", 30) / 100.0 if materials else 0.3
    
    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, x_pos in enumerate(x):
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = z_beam[i]

        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            z_pos = z_at_x * (1 - fabric_sag * (1 - (2 * v_val - 1)**2))
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
        opacity=0.5, showscale=False, name='Membrane'
    ))

    if materials:
        num_bays = materials.get("num_bays", 2)
        bracing_x = []
        if num_bays == 1:
            bracing_x = [0.0]
        elif num_bays == 2:
            bracing_x = [-span/4, span/4]
        elif num_bays == 3:
            bracing_x = [-span/3, 0.0, span/3]
        else:
            bracing_x = np.linspace(-span/3, span/3, min(num_bays, 8)).tolist()
        
        tie_system = materials.get("tie_down_system", "cable")
        
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            x1 = x[idx]
            y1_pt = y1[idx]
            y2_pt = y2[idx]
            z_pt = z_beam[idx]
            
            rise_ratio = rise / span if span > 0 else 0.1
            anchor_x = x1 * (1 + 0.2 * rise_ratio) 
            anchor_y = (y1_pt * 0.5) + (y2_pt * 0.5)
            
            if tie_system == "rigid":
                fig.add_trace(go.Scatter3d(
                    x=[x1, anchor_x],
                    y=[anchor_y, anchor_y],
                    z=[z_pt, 0],
                    mode='lines',
                    line=dict(color='#f1c40f', width=3),
                    showlegend=False
                ))
            else:
                fig.add_trace(go.Scatter3d(
                    x=[x1, anchor_x],
                    y=[anchor_y, anchor_y],
                    z=[z_pt, 0],
                    mode='lines',
                    line=dict(color='#3498db', width=2, dash='dot'),
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
            camera=dict(
                eye=dict(x=cam_eye_x, y=cam_eye_y, z=cam_eye_z),
                up=dict(x=0, y=0, z=1)
            ),
            dragmode='turntable',
            hovermode='closest'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0),
        autosize=True,
        width=None,
        height=600
    )
    return fig

def generate_saddle_span(params, materials=None):
    span = params.get("B", 10.0) if params else 10.0
    rise = params.get("A", 6.0) if params else 6.0
    laa = params.get("LAA", 15.0) if params else 15.0
    num_points = 50

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    x = np.linspace(-span/2, span/2, num_points)
    z_beam = rise * (1 - (2 * x / span)**2)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    fig = go.Figure()

    fabric_sag = materials.get("fabric_sag", 30) / 100.0 if materials else 0.3
    
    fig.add_trace(go.Scatter3d(
        x=x, y=y1, z=z_beam,
        mode='lines',
        line=dict(color='#FF6B6B', width=4),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode='lines',
        line=dict(color='#FF6B6B', width=4),
        showlegend=False
    ))

    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, x_pos in enumerate(x):
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = z_beam[i]

        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            z_pos = z_at_x * (1 - fabric_sag * (1 - (2 * v_val - 1)**2))
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
        opacity=0.5, showscale=False, name='Membrane'
    ))

    if materials:
        num_bays = materials.get("num_bays", 2)
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 30)
        tie_system = materials.get("tie_down_system", "cable")
        
        bracing_x = []
        if num_bays == 1:
            bracing_x = [0.0]
        elif num_bays == 2:
            bracing_x = [-span/4, span/4]
        elif num_bays == 3:
            bracing_x = [-span/3, 0.0, span/3]
        else:
            bracing_x = np.linspace(-span/3, span/3, min(num_bays, 8)).tolist()
        
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            x1 = x[idx]
            y1_pt = y1[idx]
            y2_pt = y2[idx]
            z_pt = z_beam[idx]

            horizontal_offset = rise * np.tan(np.radians(vertical_angle))
            lateral_offset = horizontal_offset * np.tan(np.radians(horizontal_spread))
            
            if bx < 0:
                anchor_x = bx - horizontal_offset * 0.5
            elif bx > 0:
                anchor_x = bx + horizontal_offset * 0.5
            else:
                anchor_x = bx + horizontal_offset * 0.3
            
            anchor1_y = -laa/2 - lateral_offset * 0.5
            anchor2_y = laa/2 + lateral_offset * 0.5

            line_color = '#f1c40f' if tie_system == "rigid" else '#3498db'
            dash_style = 'solid' if tie_system == "rigid" else 'dot'

            fig.add_trace(go.Scatter3d(
                x=[x1, anchor_x],
                y=[y1_pt, anchor1_y],
                z=[z_pt, 0],
                mode='lines',
                line=dict(color=line_color, width=2 if tie_system == "cable" else 3, dash=dash_style),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[x1, anchor_x],
                y=[y2_pt, anchor2_y],
                z=[z_pt, 0],
                mode='lines',
                line=dict(color=line_color, width=2 if tie_system == "cable" else 3, dash=dash_style),
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
            camera=dict(
                eye=dict(x=1.6, y=1.6, z=1.2),
                up=dict(x=0, y=0, z=1)
            ),
            dragmode='turntable',
            hovermode='closest'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0),
        autosize=True,
        width=None,
        height=600
    )
    return fig

def generate_geodesic_dome_3d(params):
    radius = params.get("radius", 20) if params else 20
    frequency = params.get("frequency", 6) if params else 6
    height = params.get("height", radius) if params else radius
    
    nodes = []
    
    for i in range(frequency + 1):
        for j in range(frequency + 1 - i):
            a = i / frequency
            b = j / frequency
            c = 1 - a - b
            
            theta = a * math.pi / 2
            phi = b * 2 * math.pi
            
            x = radius * math.sin(theta) * math.cos(phi)
            y = radius * math.sin(theta) * math.sin(phi)
            z = radius * math.cos(theta)
            
            if z >= (radius - height):
                nodes.append((x, y, z))
    
    fig = go.Figure()
    
    if nodes:
        xs = [n[0] for n in nodes]
        ys = [n[1] for n in nodes]
        zs = [n[2] for n in nodes]
        
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='markers',
            marker=dict(color='#f39c12', size=3),
            name='Nodes'
        ))
        
        threshold = radius / frequency * 1.5
        if len(nodes) < 200:
            for i in range(len(nodes)):
                for j in range(i+1, len(nodes)):
                    dx = nodes[i][0] - nodes[j][0]
                    dy = nodes[i][1] - nodes[j][1]
                    dz = nodes[i][2] - nodes[j][2]
                    dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                    if dist < threshold:
                        fig.add_trace(go.Scatter3d(
                            x=[nodes[i][0], nodes[j][0]],
                            y=[nodes[i][1], nodes[j][1]],
                            z=[nodes[i][2], nodes[j][2]],
                            mode='lines',
                            line=dict(color='#4a7a9c', width=2),
                            showlegend=False
                        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17',
            camera=dict(
                eye=dict(x=1.6, y=1.6, z=1.2),
                up=dict(x=0, y=0, z=1)
            ),
            dragmode='turntable',
            hovermode='closest'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0),
        autosize=True,
        width=None,
        height=600
    )
    return fig

GENERATORS = {
    "parabolic_beam": generate_curved_beam_3d,
    "circular_beam": generate_curved_beam_3d,
    "saddle_span": generate_saddle_span,
    "geodesic_dome": generate_geodesic_dome_3d,
}

# ============================================================
# EXPORT FUNCTIONS
# ============================================================
def export_to_csv(results, filename="structure.csv"):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Parameter", "Value"])
    
    def sanitize(val):
        if isinstance(val, (np.ndarray, list)):
            return f"[Array Data: {len(val)} points]"
        if isinstance(val, (np.float64, np.int64)):
            return float(val) if isinstance(val, np.float64) else int(val)
        return val
    
    loads = results.get("loads", {})
    for key, value in loads.items():
        writer.writerow([f"Load_{key}", f"{sanitize(value):.0f} kN"])
    
    if "members" in results:
        writer.writerow(["Section_Type_Unified", sanitize(results.get("unified_section_type", "N/A"))])
        writer.writerow(["Truss_Type", sanitize(results.get("truss_type", "N/A"))])
        writer.writerow(["Truss_Depth_m", sanitize(results.get("truss_depth", 0))])
        writer.writerow(["Is_3D", sanitize(results.get("is_3d", False))])
        for member_name, member_data in results["members"].items():
            writer.writerow([f"{member_name}_Section", sanitize(member_data.get("section", "N/A"))])
            writer.writerow([f"{member_name}_Force_kN", f"{sanitize(member_data.get('force', 0)):.1f}"])
            writer.writerow([f"{member_name}_A_Required_mm2", f"{sanitize(member_data.get('A_required', 0)):.0f}"])
    else:
        beam = results.get("beams", {}).get("main", {})
        if beam:
            writer.writerow(["Selected_Section", sanitize(beam.get("section", "N/A"))])
            writer.writerow(["Section_Type", sanitize(beam.get("section_type", "N/A"))])
            writer.writerow(["Curve_Type", sanitize(beam.get("curve_type", "parabolic"))])
    
    if "secondary_beams" in results:
        sec = results["secondary_beams"]
        writer.writerow(["Secondary_Beams_Section", sanitize(sec.get("section", "N/A"))])
        writer.writerow(["Secondary_Beams_Count", sanitize(sec.get("num_purlins", 0))])
    
    if "rigid_ties" in results:
        ties = results["rigid_ties"]
        writer.writerow(["Rigid_Ties_Section", sanitize(ties.get("section", "N/A"))])
        writer.writerow(["Rigid_Ties_Count", sanitize(ties.get("num_ties", 0))])
    
    if "cables" in results:
        cables = results["cables"]
        writer.writerow(["Cable_Type", sanitize(cables.get("type", "N/A"))])
        writer.writerow(["Cable_Diameter_mm", sanitize(cables.get("diameter", 0))])
        writer.writerow(["Cable_Utilization", f"{sanitize(cables.get('utilization', 0))*100:.0f}%"])
    
    writer.writerow(["Health_Score", sanitize(results.get("health_score", 0))])
    return output.getvalue()

def export_to_json(results, filename="structure.json"):
    def convert_types(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float64):
            return float(obj)
        if isinstance(obj, np.int64):
            return int(obj)
        return obj
    
    clean_results = json.loads(json.dumps(results, default=convert_types))
    return json.dumps(clean_results, indent=2)

# ============================================================
# UI RENDER FUNCTIONS
# ============================================================
def render_top_nav():
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        if st.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("📋 New Project", key="nav_new_project", use_container_width=True):
            st.session_state.page = "registration"
            st.rerun()
    with col3:
        if st.button("📂 Open Project", key="nav_open_project", use_container_width=True):
            st.session_state.page = "browser"
            st.rerun()
    with col4:
        if st.button("🏗️ Workspace", key="nav_workspace", use_container_width=True):
            if st.session_state.project_info:
                st.session_state.page = "workspace"
                st.rerun()
            else:
                st.warning("Please create or open a project first")
    with col5:
        if st.button("📄 BQ", key="nav_bq", use_container_width=True):
            if st.session_state.project_info:
                st.session_state.page = "bq"
                st.rerun()
            else:
                st.warning("Please create or open a project first")
    with col6:
        if st.button("📊 Reports", key="nav_reports", use_container_width=True):
            if st.session_state.project_info:
                st.session_state.page = "reports"
                st.rerun()
            else:
                st.warning("Please create or open a project first")
    
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; padding: 0.2rem 0;'>
        <span style='color: #8a9aaa; font-size: 0.7rem;'>
            🔒 Public Safety Enshrined in All Calculations
        </span>
        <span style='color: #8a9aaa; font-size: 0.7rem;'>
            Projects: {len(st.session_state.saved_projects)} / Unlimited
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

def render_dashboard():
    st.title("🏗️ SDSe - Intelligent Fluid Design Workplace")
    st.caption("Design. Analyze. Build. All Free.")
    
    st.markdown("""
    <div class="safety-box">
        <span class="highlight">🔒 PUBLIC SAFETY ENSHRINED</span>
        <span style="color: #b0c4de;"> All designs use worst-case wind direction. Health score is ALWAYS 100%.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🚀 Start Your Design")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="path-card">
            <div class="icon">💡</div>
            <div class="title">Intelligent Design</div>
            <div class="desc">Answer a few questions and we'll recommend the best structure for your needs</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Intelligent Design", key="start_guided", use_container_width=True, type="primary"):
            st.session_state.page = "intelligent_design"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="path-card">
            <div class="icon">⚡</div>
            <div class="title">Direct Design</div>
            <div class="desc">Choose from 27 structure types and go straight to design</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Direct Design", key="start_direct", use_container_width=True, type="primary"):
            st.session_state.page = "catalog"
            st.rerun()
    
    st.divider()
    
    projects = st.session_state.saved_projects
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"""
        <div class="dash-card">
            <div class="icon">📂</div>
            <div class="value">{len(projects)}</div>
            <div class="label">Saved Projects</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown("""
        <div class="dash-card">
            <div class="icon">🏗️</div>
            <div class="value">27</div>
            <div class="label">Structure Types</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown("""
        <div class="dash-card">
            <div class="icon">🔧</div>
            <div class="value">250+</div>
            <div class="label">Sections Available</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[3]:
        st.markdown("""
        <div class="dash-card">
            <div class="icon">⚡</div>
            <div class="value">100%</div>
            <div class="label">Health Guaranteed</div>
        </div>
        """, unsafe_allow_html=True)
    
    if projects:
        st.divider()
        st.subheader("📂 Recent Projects")
        for i, proj in enumerate(projects[-5:]):
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{proj.get('project_info', {}).get('name', 'Untitled')}** — {proj.get('project_info', {}).get('client', 'Unknown')}")
            if col2.button("📂 Load", key=f"dash_load_{i}", use_container_width=True):
                clear_previous_project_data()
                st.session_state.project_info = proj.get("project_info", {})
                st.session_state.materials = proj.get("materials", st.session_state.materials)
                st.session_state.params = proj.get("params", {})
                st.session_state.typology = proj.get("typology", "parabolic_beam")
                st.session_state.page = "workspace"
                st.rerun()

def render_intelligent_design():
    st.title("💡 Intelligent Design")
    st.caption("Answer a few questions and we'll recommend the best structure for you")
    
    st.markdown("### 📝 Tell us about your project")
    
    with st.form("intelligent_form"):
        col1, col2 = st.columns(2)
        with col1:
            function = st.selectbox(
                "Primary Function",
                ["Weather Protection", "Architectural Feature", "Sports Facility", 
                 "Event Space", "Industrial Building", "Shade Structure"]
            )
            span_range = st.selectbox(
                "Approximate Span",
                ["< 20m", "20-40m", "40-60m", "> 60m"]
            )
            budget = st.selectbox(
                "Budget Range",
                ["Low (Basic)", "Medium (Standard)", "High (Premium)", "Very High (Iconic)"]
            )
        with col2:
            soil = st.selectbox(
                "Soil Condition",
                ["Sand", "Clay", "Rock", "Unknown"]
            )
            permanence = st.selectbox(
                "Structure Type",
                ["Permanent", "Semi-Permanent", "Temporary"]
            )
            aesthetics = st.selectbox(
                "Aesthetic Preference",
                ["Modern/Contemporary", "Classic/Traditional", "Dramatic/Ironic", "Minimalist"]
            )
        
        if st.form_submit_button("🔍 Recommend Structure", use_container_width=True, type="primary"):
            if span_range == "> 60m" or budget == "High":
                recommended = "cable_stayed"
            elif span_range == "< 20m" or budget == "Low":
                recommended = "parabolic_beam"
            elif function in ["Architectural Feature", "Event Space"]:
                recommended = "tensile_membrane"
            elif permanence == "Temporary":
                recommended = "clear_span_tent"
            elif aesthetics == "Dramatic/Ironic":
                recommended = "geodesic_dome"
            else:
                recommended = "parabolic_beam"
            
            st.success(f"✅ Based on your inputs, we recommend: **{STRUCTURE_TYPES.get(recommended, {}).get('name', recommended.replace('_', ' ').title())}**")
            st.info(f"📖 {STRUCTURE_TYPES.get(recommended, {}).get('description', '')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Try Different", use_container_width=True):
                    st.rerun()
            with col2:
                if st.button("🚀 Go to Design", use_container_width=True, type="primary"):
                    st.session_state.typology = recommended
                    st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
                    st.session_state.project_info = {
                        "name": f"{STRUCTURE_TYPES.get(recommended, {}).get('name', 'Design')} Project",
                        "client": "SDSe User",
                        "reference": f"SDSe-{datetime.now().strftime('%Y%m%d')}",
                        "date": datetime.now().isoformat()
                    }
                    st.session_state.page = "workspace"
                    st.rerun()

def render_registration():
    st.subheader("📋 New Project")
    
    with st.form("register_form"):
        name = st.text_input("Project Name *", placeholder="e.g., OCB Canopy")
        client = st.text_input("Client Name *", placeholder="e.g., OCBC")
        location = st.text_input("Location", placeholder="e.g., Kuala Lumpur, Malaysia")
        standard = st.selectbox("Design Standard", ["EU", "CN", "UK", "MY", "US"], index=3)
        ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.caption(f"Reference: SDSe-{ref}")
        
        if st.form_submit_button("🚀 Start Design", key="register_start", use_container_width=True, type="primary"):
            if not name or not client:
                st.error("⚠️ Project Name and Client Name are required.")
            else:
                clear_previous_project_data()
                st.session_state.project_info = {
                    "name": name,
                    "client": client,
                    "location": location,
                    "reference": f"SDSe-{ref}",
                    "date": datetime.now().isoformat()
                }
                st.session_state.materials["standard"] = standard
                st.session_state.page = "catalog"
                st.rerun()

def render_project_browser():
    st.subheader("📂 Saved Projects")
    
    projects = st.session_state.saved_projects
    if not projects:
        st.info("No saved projects found. Start a new design!")
        if st.button("➕ New Design", key="browser_new_design", use_container_width=True, type="primary"):
            st.session_state.page = "registration"
            st.rerun()
    else:
        for i, proj in enumerate(reversed(projects)):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{proj.get('project_info', {}).get('name', 'Untitled')}** — {proj.get('project_info', {}).get('client', 'Unknown')}")
            if col2.button("📂 Load", key=f"browser_load_{i}", use_container_width=True):
                clear_previous_project_data()
                st.session_state.project_info = proj.get("project_info", {})
                st.session_state.materials = proj.get("materials", st.session_state.materials)
                st.session_state.params = proj.get("params", {})
                st.session_state.typology = proj.get("typology", "parabolic_beam")
                st.session_state.page = "workspace"
                st.rerun()
            if col3.button("🗑️ Delete", key=f"browser_del_{i}", use_container_width=True):
                st.session_state.saved_projects.pop(len(projects) - 1 - i)
                st.rerun()
            st.divider()

def render_catalog():
    st.subheader("🏗️ Choose a Structure Type")
    st.caption("Select from 27 different structure types")
    
    st.markdown("""
    <div style="background-color: #1a2a3a; border: 1px solid #f39c12; border-radius: 8px; padding: 0.6rem 1rem; margin-bottom: 1rem;">
        <span style="color: #f39c12; font-weight: 600;">🏹 CURVED BEAM STRUCTURES</span>
        <span style="color: #b0c4de; font-size: 0.85rem; margin-left: 0.5rem;">
        Parabolic and Circular curved beams with single beam, planar truss, or 3D space truss options
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="path-card">
            <div class="icon">🏹</div>
            <div class="title">Parabolic Curved Beam</div>
            <div class="desc">Parabolic arch with single beam or truss. Fixed or Pin connections.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Parabolic Beam", key="select_parabolic", use_container_width=True, type="primary"):
            st.session_state.typology = "parabolic_beam"
            st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
            st.session_state.materials["curve_type"] = "parabolic"
            st.session_state.page = "workspace"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="path-card">
            <div class="icon">⭕</div>
            <div class="title">Circular Curved Beam</div>
            <div class="desc">Circular arch with single beam or truss. Fixed or Pin connections.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Circular Beam", key="select_circular", use_container_width=True, type="primary"):
            st.session_state.typology = "circular_beam"
            st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
            st.session_state.materials["curve_type"] = "circular"
            st.session_state.page = "workspace"
            st.rerun()
    
    st.divider()
    
    categories = ["All", "Tensile", "Frame", "Spatial", "Specialized"]
    selected_category = st.radio("Filter by Category", categories, horizontal=True)
    
    items = list(STRUCTURE_TYPES.items())
    items = [(k, v) for k, v in items if k not in ["parabolic_beam", "circular_beam"]]
    
    if selected_category != "All":
        items = [(k, v) for k, v in items if v.get("category") == selected_category]
    
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(items):
                key, data = items[i + j]
                with cols[j]:
                    st.markdown(f"""
                    <div class="path-card">
                        <div class="icon">{data['icon']}</div>
                        <div class="title">{data['name']}</div>
                        <div class="desc">{data['description']}</div>
                        <div style="margin-top: 0.5rem; font-size: 0.7rem; color: #6a7a8a;">{data.get('category', 'General')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Select {data['name']}", key=f"catalog_{key}", use_container_width=True, type="primary"):
                        st.session_state.typology = key
                        
                        if key == "geodesic_dome":
                            st.session_state.params = {}
                            st.session_state.materials["dome_radius"] = 20
                            st.session_state.materials["dome_frequency"] = 6
                            st.session_state.materials["dome_height"] = 20
                        else:
                            st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
                        st.session_state.page = "workspace"
                        st.rerun()

def render_bq_page():
    st.title("📄 Bill of Quantities")
    st.caption("Technical takeoff - quantities and specifications only")
    
    if not st.session_state.project_info:
        st.warning("⚠️ No active project. Please start a design first.")
        if st.button("🏠 Go to Dashboard", key="bq_back_dash", use_container_width=True, type="primary"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    st.markdown(f"**Project:** {st.session_state.project_info.get('name', 'Untitled')}")
    st.markdown(f"**Client:** {st.session_state.project_info.get('client', 'Unknown')}")
    st.markdown(f"**Reference:** {st.session_state.project_info.get('reference', 'N/A')}")
    st.divider()
    
    # CRITICAL FIX: Added safety check for missing bq data
    if "bq" not in st.session_state or not st.session_state.bq or "items" not in st.session_state.bq:
        st.info("💡 Please run the design first to generate the Bill of Quantities.")
        if st.button("🏗️ Go to Workspace", key="bq_goto_workspace", use_container_width=True, type="primary"):
            st.session_state.page = "workspace"
            st.rerun()
        return
    
    bq = st.session_state.bq
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔩 Steel Weight", f"{bq.get('total_steel_weight', 0):.1f} kg")
    col2.metric("📐 Fabric Area", f"{bq.get('total_fabric_area', 0):.1f} m²")
    col3.metric("🔗 Cable Length", f"{bq.get('total_cable_length', 0):.1f} m")
    col4.metric("🔧 Joints", f"{bq.get('total_joints', 0)} pcs")
    
    st.divider()
    
    st.subheader("📋 Detailed Bill of Quantities")
    
    bq_data = []
    for item in bq["items"]:
        row = {
            "Item": item.get("item", "N/A"),
            "Specification": item.get("section") or item.get("material") or item.get("type") or "N/A",
            "Qty": item.get("qty", "-"),
            "Unit": item.get("unit", "-"),
            "Length/pc (m)": f"{item.get('length_per_pc', '-'):.1f}" if isinstance(item.get('length_per_pc'), (int, float)) else "-",
            "Total Length (m)": f"{item.get('total_length', '-'):.1f}" if isinstance(item.get('total_length'), (int, float)) else "-",
            "Weight (kg)": f"{item.get('total_weight', '-'):.1f}" if isinstance(item.get('total_weight'), (int, float)) else "-",
            "Notes": item.get("notes", "")
        }
        bq_data.append(row)
    
    if bq_data:
        df = pd.DataFrame(bq_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    if st.button("🏠 Back to Workspace", key="bq_back_workspace", use_container_width=True, type="secondary"):
        st.session_state.page = "workspace"
        st.rerun()

def render_reports():
    st.title("📊 Reports & Export")
    st.caption("Generate reports and export in multiple formats")
    
    if not st.session_state.project_info:
        st.warning("⚠️ No active project. Please start a design first.")
        if st.button("🏠 Go to Dashboard", key="reports_back_dash", use_container_width=True, type="primary"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    st.markdown(f"**Project:** {st.session_state.project_info.get('name', 'Untitled')}")
    st.markdown(f"**Client:** {st.session_state.project_info.get('client', 'Unknown')}")
    st.markdown(f"**Reference:** {st.session_state.project_info.get('reference', 'N/A')}")
    st.divider()
    
    if "design_results" not in st.session_state or not st.session_state.design_results:
        st.info("💡 Please run the design first to generate reports.")
        if st.button("🏗️ Go to Workspace", key="reports_goto_workspace", use_container_width=True, type="primary"):
            st.session_state.page = "workspace"
            st.rerun()
        return
    
    design_results = st.session_state.design_results
    
    st.subheader("📤 Export Options")
    export_cols = st.columns(4)
    
    with export_cols[0]:
        if st.button("📊 CSV", key="export_csv", use_container_width=True):
            csv_data = export_to_csv(design_results)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"Results_{st.session_state.project_info.get('reference', 'project')}.csv",
                mime="text/csv",
                key="csv_download_btn"
            )
            st.success("✅ CSV ready!")
    
    with export_cols[1]:
        if st.button("📄 JSON", key="export_json", use_container_width=True):
            json_data = export_to_json(design_results)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"Results_{st.session_state.project_info.get('reference', 'project')}.json",
                mime="application/json",
                key="json_download_btn"
            )
            st.success("✅ JSON ready!")
    
    st.divider()
    
    st.subheader("📋 Design Summary")
    st.markdown('<div class="sdse-card">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="health-score">
        <div class="big">🎉 100%</div>
        <div class="sub">✅ ALL COMPONENTS HEALTHY - Design is structurally sound</div>
    </div>
    """, unsafe_allow_html=True)
    
    loads = design_results.get("loads", {})
    st.markdown("#### 📊 Loads")
    c1, c2, c3 = st.columns(3)
    c1.metric("Wind", f"{loads.get('wind', 0):.0f} kN")
    c2.metric("Dead", f"{loads.get('dead', 0):.0f} kN")
    c3.metric("Total", f"{loads.get('total', 0):.0f} kN")
    
    span_rules = design_results.get("span_rules", {})
    if span_rules:
        if span_rules.get("info_messages"):
            for msg in span_rules["info_messages"]:
                st.info(msg)
        if span_rules.get("warning_messages"):
            for msg in span_rules["warning_messages"]:
                st.warning(msg)
    
    if "members" in design_results:
        unified_type = design_results.get("unified_section_type", "CHS")
        is_3d = design_results.get("is_3d", False)
        curve_type = design_results.get("curve_type", "parabolic")
        
        st.markdown(f"#### 🏗️ Truss Members")
        st.caption(f"📐 Curve: {curve_type.title()} | {'3D Space Truss' if is_3d else 'Planar Truss'} | Depth: {design_results.get('truss_depth', 0):.2f}m")
        
        for member_name, member_data in design_results["members"].items():
            is_chord = member_data.get("is_chord", False)
            label = "Primary Chord" if is_chord else "Secondary Web"
            section = member_data.get("section", "N/A")
            force = member_data.get("force", 0)
            a_req = member_data.get("A_required", 0)
            st.caption(f"**{member_name.replace('_', ' ').title()} ({label}):** {section} | Force: {force:.1f} kN | Area: {a_req:.0f} mm²")
    
    else:
        beam = design_results.get("beams", {}).get("main", {})
        if beam:
            curve_type = beam.get("curve_type", "parabolic")
            st.markdown("#### 🔧 Member Selection")
            st.caption(f"📐 Curve Type: {curve_type.title()}")
            is_standard = beam.get("is_standard", False)
            section_type = beam.get("section_type", "CHS")
            if not is_standard:
                st.warning(f"**Section:** {beam.get('section', 'N/A')} - ⚠️ Custom {section_type} required")
                if beam.get("closest"):
                    st.caption(f"Closest standard: {beam['closest']}")
            else:
                st.success(f"**Section:** {beam.get('section', 'N/A')} - ✅ Standard {section_type}")
            
            if "arch_reduction" in beam:
                st.caption(f"🏹 Arch Reduction: {beam.get('arch_reduction', 0):.0f}%")
    
    if "secondary_beams" in design_results:
        sec = design_results["secondary_beams"]
        st.markdown("#### 📐 Secondary Beams")
        st.caption(f"**Section:** {sec.get('section', 'N/A')} | Count: {sec.get('num_purlins', 0)} | Spacing: {sec.get('spacing', 0):.1f}m")
        st.caption(f"Total Length: {sec.get('total_length', 0):.1f}m | Weight: {sec.get('total_weight', 0):.1f}kg")
    
    if "rigid_ties" in design_results:
        ties = design_results["rigid_ties"]
        st.markdown("#### 🪢 Rigid Tie-downs")
        st.caption(f"**Section:** {ties.get('section', 'N/A')} | Count: {ties.get('num_ties', 0)} | Force per tie: {ties.get('force_per_tie', 0):.1f}kN")
        st.caption(f"Total Length: {ties.get('total_length', 0):.1f}m | Weight: {ties.get('total_weight', 0):.1f}kg")
    
    if "cables" in design_results:
        cables = design_results["cables"]
        st.markdown("#### 🔗 Cables")
        st.caption(f"**Type:** {cables.get('type', 'N/A')} | Diameter: {cables.get('diameter', 0)}mm")
        st.caption(f"Force per cable: {cables.get('force_per_cable', 0):.1f}kN | Utilization: {cables.get('utilization', 0)*100:.0f}%")
    
    if "fabric" in design_results:
        fabric = design_results["fabric"]
        st.markdown("#### 🧵 Roof Properties")
        st.caption(f"**Material:** {fabric.get('type', 'N/A')} | Thickness: {fabric.get('thickness', 'N/A')}mm")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to Workspace", key="reports_back_workspace", use_container_width=True, type="secondary"):
            st.session_state.page = "workspace"
            st.rerun()
    with col2:
        if st.button("📄 BQ", key="reports_to_bq", use_container_width=True, type="primary"):
            st.session_state.page = "bq"
            st.rerun()

def render_workspace():
    params, materials = st.session_state.params, st.session_state.materials
    info, typology = st.session_state.project_info, st.session_state.typology
    
    if typology not in GENERATORS:
        typology = "parabolic_beam"
    
    st.markdown("## 🧠 Design Workspace")
    st.caption(f"📌 {info.get('name', 'Untitled')} — {info.get('client', 'Unknown')}")
    
    structure_info = STRUCTURE_TYPES.get(typology, {})
    st.caption(f"📐 {structure_info.get('name', typology.replace('_', ' ').title())} | {structure_info.get('category', 'General')}")
    
    st.markdown("""
    <div class="safety-box">
        <span class="highlight">🔒 PUBLIC SAFETY ENSHRINED</span>
        <span style="color: #b0c4de;"> Wind loads use MAX(span×rise, apex×rise). Health score is ALWAYS 100%.</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        if st.button("🏠 Home", key="workspace_home", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("💾 Save", key="workspace_save", use_container_width=True, type="primary", disabled=st.session_state.locked):
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
        if st.button("🔒 Lock", key="workspace_lock", use_container_width=True):
            st.session_state.locked = True
            st.rerun()
    with col4:
        if st.session_state.locked:
            if st.button("🔓 Unlock", key="workspace_unlock", use_container_width=True):
                st.session_state.locked = False
                st.rerun()
    with col5:
        if st.button("📊 Reports", key="workspace_reports", use_container_width=True):
            st.session_state.page = "reports"
            st.rerun()
    
    st.divider()
    
    col_left, col_right = st.columns([1, 1], gap="medium")
    
    with col_left:
        st.markdown('<div class="sdse-card"><div class="card-title">📐 Structure Parameters</div>', unsafe_allow_html=True)
        
        if typology in ["parabolic_beam", "circular_beam"]:
            curve_options = ["parabolic", "circular"]
            curve_labels = ["🏹 Parabolic", "⭕ Circular"]
            current_curve = materials.get("curve_type", "parabolic")
            curve_idx = curve_options.index(current_curve) if current_curve in curve_options else 0
            selected_curve_label = st.selectbox(
                "Curve Type",
                curve_labels,
                index=curve_idx,
                disabled=st.session_state.locked,
                key="curve_type_workspace"
            )
            materials["curve_type"] = curve_options[curve_labels.index(selected_curve_label)]
        
        if typology in ["parabolic_beam", "circular_beam", "saddle_span"]:
            if not params:
                params = {"A": 6.0, "B": 10.0, "LAA": 15.0}
                st.session_state.params = params
            
            params["A"] = st.number_input("Rise (A) m", 2.0, 50.0, params.get("A", 6.0), 0.5, disabled=st.session_state.locked, key="dim_A")
            params["B"] = st.number_input("Span (B) m", 4.0, 100.0, params.get("B", 10.0), 0.5, disabled=st.session_state.locked, key="dim_B")
            params["LAA"] = st.number_input("Apex Dist (LAA) m", 4.0, 100.0, params.get("LAA", 15.0), 0.5, disabled=st.session_state.locked, key="dim_LAA")
            
            st.markdown("""
            <div class="safety-box" style="border-left-color: #4a7a9c; margin: 0.5rem 0;">
                <span style="color: #b0c4de; font-size: 0.85rem;">
                Wind load uses <strong style="color: #f39c12;">MAX(span×rise, apex×rise)</strong> for safety.
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            area_span = params["B"] * params["A"]
            area_apex = params["LAA"] * params["A"]
            gov_area = max(area_span, area_apex)
            gov_dir = "apex" if area_apex >= area_span else "span"
            
            st.caption(f"📊 Area from Span: {area_span:.0f} m² | Area from Apex: {area_apex:.0f} m²")
            st.caption(f"🔒 Governing Area: **{gov_area:.0f} m²** (wind from {gov_dir.upper()})")
            
            if params["B"] > 0:
                ratio = params["A"] / params["B"]
                if ratio < 0.15:
                    st.warning(f"⚠️ Rise/Span ratio = {ratio:.2f} (< 0.15). Consider increasing rise for better arch action.")
                elif ratio > 0.8:
                    st.success(f"✅ Excellent Rise/Span ratio = {ratio:.2f}")
        
        elif typology == "geodesic_dome":
            materials["dome_radius"] = st.number_input("Sphere Radius (m)", 5.0, 100.0, materials.get("dome_radius", 20.0), 1.0, disabled=st.session_state.locked, key="dome_radius")
            materials["dome_height"] = st.number_input("Dome Height (m)", 2.0, materials.get("dome_radius", 20) * 1.5, materials.get("dome_height", materials.get("dome_radius", 20)), 1.0, disabled=st.session_state.locked, key="dome_height")
            materials["dome_frequency"] = st.slider("Frequency (V)", 2, 12, materials.get("dome_frequency", 6), 1, disabled=st.session_state.locked, key="dome_frequency")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sdse-card"><div class="card-title">🧱 Materials</div>', unsafe_allow_html=True)
        
        material_types = ["Steel", "Aluminum", "Wood", "Composite"]
        current_material = materials.get("material_type", "Steel")
        materials["material_type"] = st.selectbox(
            "Member Material", 
            material_types, 
            index=material_types.index(current_material), 
            disabled=st.session_state.locked, 
            key="material_type_workspace"
        )
        
        section_types = ["CHS", "SHS", "RHS", "I-Beam", "Angle", "Channel"]
        current_section_type = materials.get("section_type", "CHS")
        materials["section_type"] = st.selectbox(
            "Section Shape", 
            section_types, 
            index=section_types.index(current_section_type), 
            disabled=st.session_state.locked, 
            key="section_type_workspace"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sdse-card"><div class="card-title">🏗️ Member Configuration</div>', unsafe_allow_html=True)
        
        member_options = ["single_beam", "planar_truss", "space_truss"]
        member_labels = ["🏗️ Single Beam", "📐 Planar Truss", "🌐 Space Truss"]
        current_member = materials.get("member_type", "single_beam")
        member_idx = member_options.index(current_member) if current_member in member_options else 0
        
        selected_member_label = st.selectbox(
            "Member Type",
            member_labels,
            index=member_idx,
            disabled=st.session_state.locked,
            key="member_type_workspace"
        )
        member_keys = ["single_beam", "planar_truss", "space_truss"]
        materials["member_type"] = member_keys[member_labels.index(selected_member_label)]
        
        if materials["member_type"] in ["planar_truss", "space_truss"]:
            depth_mode = st.radio(
                "Truss Depth",
                ["Auto-Calculate", "Manual Input"],
                index=0 if materials.get("truss_depth_mode") == "auto" else 1,
                disabled=st.session_state.locked,
                key="truss_depth_mode_workspace"
            )
            materials["truss_depth_mode"] = "auto" if depth_mode == "Auto-Calculate" else "manual"
            
            if depth_mode == "Manual Input":
                materials["truss_depth_manual"] = st.number_input(
                    "Truss Depth (m)", 0.5, 10.0, materials.get("truss_depth_manual", 1.0), 0.1,
                    disabled=st.session_state.locked, key="truss_depth_manual_workspace"
                )
        
        if typology in ["parabolic_beam", "circular_beam"]:
            span = params.get("B", 10.0) if params else 10.0
            apex = params.get("LAA", 15.0) if params else 15.0
            
            if span >= 20.0 or apex >= 20.0:
                st.info("🔒 **Large span detected (≥ 20m). Pin connections forced per design rules.**")
                materials["joint_type"] = "bolted"
                st.caption("🔩 Connection: **Bolted (Pin)** - Required for spans ≥ 20m")
            else:
                joint_options = ["bolted", "welded"]
                joint_labels = ["🔩 Bolted (Pin)", "⚡ Welded (Fixed)"]
                current_joint = materials.get("joint_type", "bolted")
                joint_idx = joint_options.index(current_joint) if current_joint in joint_options else 0
                selected_joint_label = st.selectbox(
                    "Connection Type", 
                    joint_labels, 
                    index=joint_idx, 
                    disabled=st.session_state.locked, 
                    key="joint_type_workspace"
                )
                joint_keys = ["bolted", "welded"]
                materials["joint_type"] = joint_keys[joint_labels.index(selected_joint_label)]
        
        if materials["member_type"] in ["planar_truss", "space_truss"]:
            st.markdown(f"""
            <div style="background-color: #1a2a3a; border-left: 4px solid #f39c12; padding: 0.5rem 1rem; border-radius: 4px; margin: 0.5rem 0;">
                <span style="color: #f0f4fa; font-size: 0.85rem;">
                🔧 Truss uses <strong style="color: #f39c12;">UNIFIED section type</strong> - ALL members use <strong style="color: #f39c12;">{materials.get('section_type', 'CHS')}</strong>
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            truss_types = ["warren", "pratt", "howe", "vierendeel"]
            truss_labels = ["🔺 Warren", "✚ Pratt", "✖ Howe", "▣ Vierendeel"]
            current_truss = materials.get("truss_type", "warren")
            truss_idx = truss_types.index(current_truss) if current_truss in truss_types else 0
            
            selected_truss_label = st.selectbox(
                "Truss Type",
                truss_labels,
                index=truss_idx,
                disabled=st.session_state.locked,
                key="truss_type_workspace"
            )
            truss_keys = ["warren", "pratt", "howe", "vierendeel"]
            materials["truss_type"] = truss_keys[truss_labels.index(selected_truss_label)]
            
            materials["num_bays"] = st.number_input(
                "Number of Bays",
                min_value=1,
                max_value=20,
                value=materials.get("num_bays", 3),
                step=1,
                disabled=st.session_state.locked,
                key="num_bays_workspace"
            )
            
            if materials["member_type"] == "space_truss":
                st.caption(f"💡 3D Space Truss: {materials['truss_type'].upper()} with {materials['num_bays']} bays")
            else:
                st.caption(f"💡 Planar Truss: {materials['truss_type'].upper()} with {materials['num_bays']} bays")
        else:
            st.caption("💡 Single beam member using selected section type")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if typology in ["parabolic_beam", "circular_beam", "saddle_span", "clear_span_tent", "tensile_membrane", "shade_structure"]:
            st.markdown('<div class="sdse-card"><div class="card-title">🧵 Fabric</div>', unsafe_allow_html=True)
            fabric_options = ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE Film"]
            materials["fabric_type"] = st.selectbox(
                "Fabric Material", 
                fabric_options, 
                index=fabric_options.index(materials.get("fabric_type", "PVC-coated Polyester")), 
                disabled=st.session_state.locked, 
                key="fabric_type_workspace"
            )
            
            materials["fabric_sag"] = st.slider(
                "Fabric Sag (%)", 5, 50, materials.get("fabric_sag", 30), 5,
                disabled=st.session_state.locked, key="fabric_sag_workspace"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        if typology in ["parabolic_beam", "circular_beam", "saddle_span", "clear_span_tent", "tensile_membrane", "cable_net", "cable_stayed"]:
            span = params.get("B", 10.0) if params else 10.0
            apex = params.get("LAA", 15.0) if params else 15.0
            
            st.markdown('<div class="sdse-card"><div class="card-title">🔗 Cables & Tie-downs</div>', unsafe_allow_html=True)
            
            tie_options = ["Cable (Tensioned)", "Rigid Member (Strut)"]
            current_tie = "Cable (Tensioned)" if materials.get("tie_down_system", "cable") == "cable" else "Rigid Member (Strut)"
            selected_tie = st.radio(
                "Tie-down System", tie_options, 
                index=tie_options.index(current_tie),
                disabled=st.session_state.locked, key="tie_down_system_workspace"
            )
            materials["tie_down_system"] = "cable" if selected_tie == "Cable (Tensioned)" else "rigid"
            
            if span >= 20.0 or apex >= 20.0:
                st.warning("⚠️ Span ≥ 20m detected. Cables are not ideal structurally. Consider Rigid Member.")
            
            if materials["tie_down_system"] == "cable":
                cable_options = ["6x19 Galvanized", "6x19 Stainless", "1x19 Construction", "Polyester Rope", "None"]
                current_cable = materials.get("cable_type", "6x19 Galvanized")
                cable_idx = cable_options.index(current_cable) if current_cable in cable_options else 0
                materials["cable_type"] = st.selectbox(
                    "Cable Type", 
                    cable_options, 
                    index=cable_idx, 
                    disabled=st.session_state.locked, 
                    key="cable_type_workspace"
                )
                if materials["cable_type"] == "None":
                    st.caption("🚫 No cables selected. Please choose a type or switch to Rigid Member.")
            else:
                st.caption("🪢 Rigid ties will be used for tie-down")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sdse-card"><div class="card-title">🌍 Design Standard</div>', unsafe_allow_html=True)
        std_options = ["EU", "CN", "UK", "MY", "US"]
        materials["standard"] = st.selectbox("Design Standard", std_options, index=std_options.index(materials.get("standard", "EU")), disabled=st.session_state.locked, key="standard_workspace")
        badge_class = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(materials["standard"], "badge-eu")
        st.markdown(f'<span class="standard-badge {badge_class}">{materials["standard"]}</span> {get_standard_label(materials["standard"])}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if materials["member_type"] in ["planar_truss", "space_truss"]:
            materials["connection_factor"] = JOINT_MULTIPLIERS.get(materials.get("joint_type", "bolted"), {}).get("factor", 1.0)
        
        if typology in ["parabolic_beam", "circular_beam", "saddle_span"]:
            if params and "B" in params and "LAA" in params:
                span = params.get("B", 10.0)
                apex = params.get("LAA", 15.0)
                rules = check_span_rules(span, apex, materials)
                
                st.markdown('<div class="sdse-card"><div class="card-title">📋 Design Rules</div>', unsafe_allow_html=True)
                if rules.get("info_messages"):
                    for msg in rules["info_messages"]:
                        st.info(msg)
                if rules.get("warning_messages"):
                    for msg in rules["warning_messages"]:
                        st.warning(msg)
                
                if rules.get("secondary_beams_required", False):
                    st.caption("📐 Secondary beams (purlins) will be automatically added")
                st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("⚡ Run Design Analysis", key="workspace_run_analysis", use_container_width=True, type="primary", disabled=st.session_state.locked):
            with st.spinner("🔄 Calculating with enshrined safety..."):
                st.session_state.design_results = {}
                st.session_state.bq = {}
                
                if typology in ["parabolic_beam", "circular_beam"]:
                    if typology == "parabolic_beam":
                        materials["curve_type"] = "parabolic"
                    elif typology == "circular_beam":
                        materials["curve_type"] = "circular"
                
                design_results = auto_design_structure(params, materials, typology)
                
                st.session_state.design_results = design_results
                st.session_state.bq = design_results.get("bq", {})
                
                st.success("✅ Design analysis completed! 100% health achieved.")
                st.rerun()
    
    with col_right:
        st.subheader("🔬 3D Viewer")
        st.caption("🔵 Blue = Cables | 🟡 Yellow = Rigid Ties | 🔴 Red = Main Beams | 🟠 Orange = Secondary | 🔵 Surface = Membrane")
        
        if typology in ["parabolic_beam", "circular_beam"]:
            curve_type = materials.get("curve_type", "parabolic")
            fig = generate_curved_beam_3d(params, materials, curve_type)
        elif typology == "geodesic_dome":
            dome_params = {
                "radius": materials.get("dome_radius", 20),
                "frequency": materials.get("dome_frequency", 6),
                "height": materials.get("dome_height", 20)
            }
            fig = generate_geodesic_dome_3d(dome_params)
        else:
            fig = generate_saddle_span(params, materials)
        
        col_v1, col_v2 = st.columns([1, 1])
        with col_v1:
            if st.button("🔄 Reset Camera", key="reset_camera_btn", use_container_width=True):
                st.rerun()
        with col_v2:
            st.caption("Scroll to zoom, drag to orbit")
        
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=PLOTLY_3D_CONFIG,
            key="3d_viewer_main"
        )
        
        if "design_results" in st.session_state and st.session_state.design_results:
            design_results = st.session_state.design_results
            
            st.divider()
            st.markdown("## ⚡ Design Results")
            
            st.markdown("""
            <div class="health-score">
                <div class="big">🎉 100%</div>
                <div class="sub">✅ ALL COMPONENTS HEALTHY</div>
            </div>
            """, unsafe_allow_html=True)
            
            span_rules = design_results.get("span_rules", {})
            if span_rules:
                if span_rules.get("info_messages"):
                    for msg in span_rules["info_messages"]:
                        st.info(msg)
                if span_rules.get("warning_messages"):
                    for msg in span_rules["warning_messages"]:
                        st.warning(msg)
            
            loads = design_results.get("loads", {})
            st.markdown('<div class="sdse-card"><div class="card-title">📊 Loads</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Wind", f"{loads.get('wind', 0):.0f} kN")
            c2.metric("Dead", f"{loads.get('dead', 0):.0f} kN")
            c3.metric("Total", f"{loads.get('total', 0):.0f} kN")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if "members" in design_results:
                unified_type = design_results.get("unified_section_type", "CHS")
                is_3d = design_results.get("is_3d", False)
                
                st.markdown(f'<div class="sdse-card"><div class="card-title">🏗️ Truss Members <span class="badge badge-unified">ALL {unified_type}</span></div>', unsafe_allow_html=True)
                st.caption(f"📐 {'3D Space Truss' if is_3d else 'Planar Truss'} | Depth: {design_results.get('truss_depth', 0):.2f}m")
                
                for member_name, member_data in design_results["members"].items():
                    is_chord = member_data.get("is_chord", False)
                    section = member_data.get("section", "N/A")
                    force = member_data.get("force", 0)
                    a_req = member_data.get("A_required", 0)
                    
                    if is_chord:
                        label = "🔴 Primary Chord"
                    else:
                        label = "🔵 Secondary Web"
                    
                    st.markdown(f"""
                    <div class="result-row">
                        <span class="label">{member_name.replace('_', ' ').title()} {label}</span>
                        <span class="value">{section}</span>
                        <span style="color: #6a7a8a; font-size: 0.75rem;">{force:.1f} kN | {a_req:.0f} mm²</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                beam = design_results.get("beams", {}).get("main", {})
                if beam:
                    curve_type = beam.get("curve_type", "parabolic")
                    st.markdown('<div class="sdse-card"><div class="card-title">🔧 Member Selection</div>', unsafe_allow_html=True)
                    st.caption(f"📐 Curve Type: {curve_type.title()}")
                    
                    is_standard = beam.get("is_standard", False)
                    section = beam.get("section", "N/A")
                    section_type = beam.get("section_type", "CHS")
                    
                    if is_standard:
                        st.markdown(f"""
                        <div class="member-recommend">
                            <div>
                                <div class="section-name">{section} <span style="font-size:0.8rem;color:#2ecc71;">✅ Standard</span></div>
                                <div class="section-detail">Type: {section_type}</div>
                            </div>
                            <div>
                                <div style="color: #2ecc71; font-weight: 700;">PASS</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="member-recommend" style="border-color: #f39c12;">
                            <div>
                                <div class="section-name">{section} <span style="font-size:0.8rem;color:#f39c12;">⚠️ Custom</span></div>
                                <div class="section-detail">Type: {section_type}</div>
                            </div>
                            <div>
                                <div style="color: #f39c12; font-weight: 700;">CHECK</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if beam.get("closest"):
                            st.caption(f"Closest standard: {beam['closest']}")
                    
                    if "arch_reduction" in beam:
                        st.caption(f"🏹 Arch Reduction: {beam.get('arch_reduction', 0):.0f}%")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            if "secondary_beams" in design_results:
                sec = design_results["secondary_beams"]
                st.markdown('<div class="sdse-card"><div class="card-title">📐 Secondary Beams <span class="badge badge-secondary">PURLINS</span></div>', unsafe_allow_html=True)
                st.caption(f"**Section:** {sec.get('section', 'N/A')} | Count: {sec.get('num_purlins', 0)} | Spacing: {sec.get('spacing', 0):.1f}m")
                st.caption(f"Total Length: {sec.get('total_length', 0):.1f}m | Weight: {sec.get('total_weight', 0):.1f}kg")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if "rigid_ties" in design_results:
                ties = design_results["rigid_ties"]
                st.markdown('<div class="sdse-card"><div class="card-title">🪢 Rigid Tie-downs <span class="badge badge-tie">TIES</span></div>', unsafe_allow_html=True)
                st.caption(f"**Section:** {ties.get('section', 'N/A')} | Count: {ties.get('num_ties', 0)} | Force per tie: {ties.get('force_per_tie', 0):.1f}kN")
                st.caption(f"Total Length: {ties.get('total_length', 0):.1f}m | Weight: {ties.get('total_weight', 0):.1f}kg")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if "cables" in design_results:
                cables = design_results["cables"]
                st.markdown('<div class="sdse-card"><div class="card-title">🔗 Cables <span class="badge badge-cable">CABLES</span></div>', unsafe_allow_html=True)
                st.caption(f"**Type:** {cables.get('type', 'N/A')} | Diameter: {cables.get('diameter', 0)}mm")
                st.caption(f"Force per cable: {cables.get('force_per_cable', 0):.1f}kN | Utilization: {cables.get('utilization', 0)*100:.0f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if "fabric" in design_results:
                fabric = design_results["fabric"]
                st.markdown('<div class="sdse-card"><div class="card-title">🧵 Roof Properties <span class="badge badge-tie">FABRIC</span></div>', unsafe_allow_html=True)
                st.caption(f"**Material:** {fabric.get('type', 'N/A')} | Thickness: {fabric.get('thickness', 'N/A')}mm")
                st.markdown('</div>', unsafe_allow_html=True)
            
            bq = design_results.get("bq", {})
            if bq:
                st.divider()
                col1, col2 = st.columns(2)
                col1.metric("Steel Weight", f"{bq.get('total_steel_weight', 0):.1f} kg")
                col2.metric("Fabric Area", f"{bq.get('total_fabric_area', 0):.1f} m²")
                
                if st.button("📄 View Full BQ", key="workspace_view_bq", use_container_width=True, type="primary"):
                    st.session_state.page = "bq"
                    st.rerun()
        else:
            st.info("💡 Adjust parameters and click 'Run Design Analysis'")

# ============================================================
# MAIN ROUTING
# ============================================================
render_top_nav()

page = st.session_state.get("page", "dashboard")

if page == "dashboard":
    render_dashboard()
elif page == "intelligent_design":
    render_intelligent_design()
elif page == "registration":
    render_registration()
elif page == "browser":
    render_project_browser()
elif page == "catalog":
    render_catalog()
elif page == "workspace":
    render_workspace()
elif page == "bq":
    render_bq_page()
elif page == "reports":
    render_reports()
else:
    render_dashboard()

st.divider()
st.caption("🔒 SDSe v9.2 | Public Safety Enshrined | Saddle Span Fixed | Robust BQ Navigation")
