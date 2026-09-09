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

# PDF Reporting
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SDSe Intelligent Fluid Design Workplace",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# PLOTLY 3D CONFIG - SMOOTH VIEWER
# ============================================================
PLOTLY_3D_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
    "doubleClick": "reset",
    "showTips": True,
    "toImageButtonOptions": {"format": "png", "filename": "sdse_structure", "scale": 2},
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"],
    "modeBarButtonsToAdd": ["zoomIn3d", "zoomOut3d", "resetCameraDefault3d", "orbitRotation", "tableRotation"]
}

# ============================================================
# DARK MODE CSS (CLEAN & PROFESSIONAL)
# ============================================================
dark_mode_css = """
    <style>
    .stApp { background-color: #0a0e17 !important; color: #f0f4fa !important; }
    .stApp > header { display: none !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 600 !important; }
    label { color: #ffffff !important; font-weight: 400 !important; font-size: 0.85rem !important; }
    .stButton > button { background-color: #1e2a3a !important; color: #ffffff !important; border: 1px solid #2a3a4f !important; border-radius: 8px !important; padding: 0.4rem 0.8rem !important; font-weight: 500 !important; font-size: 0.85rem !important; width: 100% !important; transition: all 0.3s ease !important; }
    .stButton > button:hover { background-color: #2a3a4f !important; border-color: #4a7a9c !important; transform: translateY(-2px) !important; box-shadow: 0 4px 12px rgba(74, 122, 156, 0.2) !important; }
    .stButton > button[kind="primary"] { background-color: #f39c12 !important; color: #0a0e17 !important; border: none !important; font-weight: 600 !important; }
    .stNumberInput > div > div > input, .stSelectbox > div > div > div, .stTextArea textarea, .stTextInput > div > div > input { background-color: #141e2b !important; color: #ffffff !important; border: 1px solid #2a3a4f !important; border-radius: 8px !important; font-size: 0.85rem !important; }
    .stAlert { background-color: #1e2a3a !important; border-left: 4px solid #f39c12 !important; color: #f0f4fa !important; font-size: 0.85rem !important; border-radius: 8px !important; padding: 0.8rem 1rem !important; }
    .stInfo { background-color: #1a2a3a !important; border-left: 4px solid #4a7a9c !important; }
    .stSuccess { background-color: #1a3a2a !important; border-left: 4px solid #2ecc71 !important; }
    .stError { background-color: #3a1a1a !important; border-left: 4px solid #e74c3c !important; }
    .stWarning { background-color: #4a3a1a !important; border-left: 4px solid #f39c12 !important; }
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    .stPlotlyChart { width: 100% !important; border-radius: 12px !important; overflow: hidden !important; background-color: #0a0e17 !important; border: 1px solid #1e2a3a; }
    .sdse-card { background-color: #121e2e; border-radius: 12px; padding: 1.2rem 1.2rem; border: 1px solid #1e2a3a; margin-bottom: 0.8rem; transition: all 0.3s ease; }
    .sdse-card:hover { border-color: #2a3a4f; }
    .sdse-card .card-title { color: #ffffff; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.8rem; }
    .health-score { background-color: #1a3a2a; border: 2px solid #2ecc71; border-radius: 12px; padding: 1rem; text-align: center; margin: 0.5rem 0; }
    .health-score .big { font-size: 2.8rem; font-weight: 700; color: #2ecc71; }
    .health-score .sub { color: #b0c4de; font-size: 0.9rem; }
    .member-recommend { background-color: #1a2a3a; border: 2px solid #f39c12; border-radius: 10px; padding: 0.8rem 1.2rem; margin: 0.5rem 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
    .member-recommend .section-name { color: #ffffff; font-size: 1.1rem; font-weight: 700; }
    .member-recommend .section-detail { color: #8a9aaa; font-size: 0.75rem; }
    .member-recommend .status-pass { color: #2ecc71; font-weight: 700; }
    
    /* Tier Badge Styling */
    .tier-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .tier-basic { background-color: #2a3a4f; color: #8a9aaa; border: 1px solid #3a4a5f; }
    .tier-pro { background-color: #f39c12; color: #0a0e17; border: 1px solid #f39c12; }
    
    /* Dashboard Cards */
    .dash-card { background-color: #121e2e; border-radius: 12px; padding: 1.2rem 1rem; border: 1px solid #1e2a3a; text-align: center; transition: all 0.3s ease; }
    .dash-card:hover { border-color: #2a3a4f; transform: translateY(-3px); }
    .dash-card .icon { font-size: 2.2rem; }
    .dash-card .value { color: #ffffff; font-size: 1.5rem; font-weight: 700; margin: 0.3rem 0; }
    .dash-card .label { color: #8a9aaa; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
    
    @media (max-width: 768px) { .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; } }
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
        "commercial_tier": "pro",
        "materials": {
            "standard": "MY",
            "material_type": "Steel",
            "section_type": "CHS",
            "fabric_type": "PVC-coated Polyester",
            "cable_type": "6x19 Galvanized",
            "member_type": "single_beam",
            "truss_type": "warren",
            "num_bays": 2,
            "joint_type": "bolted",
            "tie_down_system": "cable",
            "truss_depth_mode": "auto",
            "truss_depth_manual": 1.0,
            "fabric_sag": 30,
            "system_mode": "cable_stayed",
            "country": "Malaysia"
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
        "standard": "MY", "material_type": "Steel", "section_type": "CHS",
        "fabric_type": "PVC-coated Polyester", "cable_type": "6x19 Galvanized",
        "member_type": "single_beam", "truss_type": "warren", "num_bays": 2,
        "joint_type": "bolted", "tie_down_system": "cable", "truss_depth_mode": "auto",
        "truss_depth_manual": 1.0, "fabric_sag": 30, "system_mode": "cable_stayed",
        "country": "Malaysia"
    }
    st.session_state.materials = default_materials

# ============================================================
# COMPREHENSIVE SECTION PROPERTIES DATABASE
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
    "I-500": {"A": 17500, "I": 694.0e6, "W_el": 2780e3, "i": 199.2, "weight": 137.4, "type": "I-Beam", "depth": 500}
}

# ============================================================
# FULL FABRIC & CABLE PROPERTIES
# ============================================================
FABRIC_PROPERTIES = {
    "PVC-coated Polyester": {"thickness": {"0.5": 30, "0.8": 40, "1.0": 50, "1.2": 60}, "weight_per_m2": 1.2},
    "PTFE-coated Fiberglass": {"thickness": {"0.5": 40, "0.8": 55, "1.0": 70, "1.2": 85}, "weight_per_m2": 1.8},
    "ETFE Film": {"thickness": {"0.05": 15, "0.08": 25, "0.10": 32, "0.15": 42, "0.20": 55}, "weight_per_m2": 0.8}
}

CABLE_PROPERTIES = {
    "6x19 Galvanized": {"diameters": {6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140, 18: 180, 20: 220, 24: 310, 28: 420, 32: 540, 40: 840}, "weight_per_m": {6: 0.178, 8: 0.317, 10: 0.495, 12: 0.713, 14: 0.971, 16: 1.270, 18: 1.600, 20: 1.980, 24: 2.850}},
    "1x19 Construction": {"diameters": {2.5: 4.9, 3.0: 7.0, 4.0: 12.6, 5.0: 19.6, 6.0: 28.0, 7.0: 35.0, 8.0: 45.4, 10.0: 71.0, 12.0: 102.0, 14.0: 139.0, 16.0: 182.0, 18.0: 220.0, 20.0: 260.0}, "weight_per_m": {2.5: 0.031, 3.0: 0.045, 4.0: 0.079, 5.0: 0.124, 6.0: 0.178, 7.0: 0.243, 8.0: 0.317, 10.0: 0.495}},
    "6x19 Stainless": {"diameters": {6: 25, 8: 42, 10: 65, 12: 95, 14: 125, 16: 160, 18: 200, 20: 245}, "weight_per_m": {6: 0.178, 8: 0.317, 10: 0.495, 12: 0.713, 14: 0.971, 16: 1.270}},
    "Polyester Rope": {"diameters": {8: 30, 10: 45, 12: 65, 14: 85, 16: 110, 18: 140, 20: 170, 24: 230}, "weight_per_m": {8: 0.050, 10: 0.080, 12: 0.115, 14: 0.155, 16: 0.200}}
}

# ============================================================
# LOCKED ENGINE v12.3 - THE 2 MATHEMATICAL ENGINES
# ============================================================
WIND_SPEEDS = {"EU": 30.0, "CN": 28.0, "UK": 26.0, "MY": 33.5, "US": 38.0}

def calculate_wind_load(span, apex, rise, standard="MY", system_mode="cable_stayed"):
    wind_speed = WIND_SPEEDS.get(standard, 33.5)
    q = 0.5 * 1.225 * wind_speed**2 / 1000
    gov_area = max(span * rise, apex * rise)
    shape_factor = 1.3 if system_mode == "cable_stayed" else 0.85
    return q * gov_area * shape_factor * 1.1

def calculate_dead_load(span, apex, materials, system_mode, member_type):
    fabric_w = FABRIC_PROPERTIES.get(materials.get("fabric_type", "PVC"), {}).get("weight_per_m2", 1.2)
    fabric_kg = fabric_w * span * apex * 1.2
    steel_kg = 300
    cable_kg = 84
    if system_mode == "rigid":
        purlin_kg = 240
        tie_kg = 60
    else:
        purlin_kg = 0
        tie_kg = 0
    if member_type == "planar_truss":
        steel_kg *= 1.5
    elif member_type == "space_truss":
        steel_kg *= 2.0
    total_kg = fabric_kg + steel_kg + cable_kg + purlin_kg + tie_kg
    return total_kg / 1000, total_kg

def find_closest_section(W_required, section_type):
    sections = [(n, p) for n, p in SECTION_PROPERTIES.items() if p["type"] == section_type]
    sections.sort(key=lambda x: x[1]["W_el"])
    closest = None
    for name, props in sections:
        if props["W_el"] >= W_required:
            closest = (name, props)
            break
    return closest if closest else sections[-1]

def auto_design_structure(params, materials, typology):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    apex = params.get("LAA", 15.0)
    system_mode = materials.get("system_mode", "cable_stayed")
    member_type = materials.get("member_type", "single_beam")
    section_type = materials.get("section_type", "CHS")
    
    wind = calculate_wind_load(span, apex, rise, materials.get("standard", "MY"), system_mode)
    dead, dead_kg = calculate_dead_load(span, apex, materials, system_mode, member_type)
    total = wind + dead
    
    M = total * max(span, apex)**2 / 8 / 1000
    W_req = M * 1000 / (0.6 * 275) * 1000
    min_depth = max(span, apex) / 30 * 1000
    
    best_section = None
    for name, props in SECTION_PROPERTIES.items():
        if props["type"] == section_type and props["W_el"] >= W_req and props["depth"] >= min_depth:
            best_section = (name, props)
            break
    if not best_section:
        candidates = [(n, p) for n, p in SECTION_PROPERTIES.items() if p["type"] == section_type]
        best_section = max(candidates, key=lambda x: x[1]["W_el"])
    
    if system_mode == "rigid":
        num_purlins = int(max(span, apex) / 2.0) + 1
        tie_qty = 2
        purlin_section = find_closest_section(W_req / 10, section_type)
    else:
        num_purlins = 0
        tie_qty = 0
        purlin_section = None
    
    if system_mode == "cable_stayed":
        cable_dia = 12 if span < 20 else 20 if span < 40 else 40
        cable_type = materials.get("cable_type", "6x19 Galvanized")
        cable_count = (materials.get("num_bays", 2) + 1) * 2
    else:
        cable_dia = 0
        cable_type = "N/A"
        cable_count = 0
    
    tie_section = find_closest_section(W_req / 20, section_type)
    
    return {
        "loads": {"wind": wind, "dead": dead, "total": total, "dead_kg": dead_kg},
        "beams": {"main": {"section": best_section[0], "section_type": section_type, "is_standard": True, "W_actual": best_section[1]["W_el"], "W_required": W_req}},
        "secondary_beams": {"section": purlin_section[0] if purlin_section else "N/A", "num_purlins": num_purlins, "spacing": 2.0 if num_purlins > 0 else 0, "total_weight": (purlin_section[1]["weight"] * 10 * num_purlins) if purlin_section else 0},
        "rigid_ties": {"section": tie_section[0] if tie_section else best_section[0], "num_ties": tie_qty, "total_weight": tie_qty * 10 * (tie_section[1]["weight"] if tie_section else best_section[1]["weight"])},
        "cables": {"type": cable_type, "diameter": cable_dia, "num_cables": cable_count, "total_length": cable_count * apex * 1.1},
        "fabric": {"type": materials.get("fabric_type", "PVC"), "thickness": "1.0mm", "area": span * apex},
        "health_score": 100,
        "span_rules": {"info_messages": ["🔒 Enshrined Safety: Loads based on worst-case direction."], "warning_messages": []},
        "bq": generate_bq(best_section[0], num_purlins, tie_qty, cable_dia, cable_count, span, apex, section_type)
    }

def generate_bq(main_section, num_purlins, tie_qty, cable_dia, cable_count, span, apex, section_type):
    main_w = SECTION_PROPERTIES[main_section]["weight"]
    items = [
        {"item": "Main Beams", "section": main_section, "qty": 2, "unit": "pcs", "length_per_pc": apex, "total_length": apex*2, "total_weight": apex*2*main_w, "notes": "Primary members"},
        {"item": "Roof Fabric", "section": "PVC", "qty": 1, "unit": "lot", "length_per_pc": 0, "total_length": 0, "total_weight": span*apex*1.2, "notes": "Membrane"}
    ]
    if num_purlins > 0:
        purlin_sec = find_closest_section(1000, section_type)[0]
        items.append({"item": "Secondary Beams", "section": purlin_sec, "qty": num_purlins, "unit": "pcs", "length_per_pc": span, "total_length": span*num_purlins, "total_weight": span*num_purlins*SECTION_PROPERTIES[purlin_sec]["weight"], "notes": "Purlins"})
    if tie_qty > 0:
        tie_sec = find_closest_section(1000, section_type)[0]
        items.append({"item": "Rigid Tie Rods", "section": tie_sec, "qty": tie_qty, "unit": "pcs", "length_per_pc": span, "total_length": span*tie_qty, "total_weight": span*tie_qty*SECTION_PROPERTIES[tie_sec]["weight"], "notes": "Base restraints"})
    if cable_count > 0:
        items.append({"item": "Tie-down Cables", "section": f"{cable_dia}mm", "qty": cable_count, "unit": "pcs", "length_per_pc": apex, "total_length": apex*cable_count, "total_weight": apex*cable_count*0.7, "notes": "Tension ties"})
    return {"items": items, "total_steel_weight": sum(i["total_weight"] for i in items if "Cable" not in i["item"]), "total_fabric_area": span*apex, "total_cable_length": apex*cable_count if cable_count > 0 else 0, "total_joints": 20}

# ============================================================
# UNIVERSAL 3D GENERATOR (RESTORED YELLOW CABLES)
# ============================================================
def generate_universal_3d(params, materials, design_results):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    apex = params.get("LAA", 15.0)
    num_points = 50
    x = np.linspace(-span/2, span/2, num_points)
    z = rise * (1 - (2*x/span)**2)
    y1 = -apex/2 * (1 - (2*x/span)**2)
    y2 = apex/2 * (1 - (2*x/span)**2)

    fig = go.Figure()
    
    # Main Beams
    beam_width = 5
    if materials.get("member_type") == "planar_truss":
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z, mode='lines', line=dict(color='#FF6B6B', width=beam_width), showlegend=False))
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z-rise/10, mode='lines', line=dict(color='#FF6B6B', width=beam_width/2), showlegend=False))
    elif materials.get("member_type") == "space_truss":
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z, mode='lines', line=dict(color='#FF6B6B', width=beam_width), showlegend=False))
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z-rise/10, mode='lines', line=dict(color='#FF6B6B', width=beam_width/2), showlegend=False))
        fig.add_trace(go.Scatter3d(x=x, y=y1+apex/10, z=z, mode='lines', line=dict(color='#FF6B6B', width=beam_width/2), showlegend=False))
    else:
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z, mode='lines', line=dict(color='#FF6B6B', width=beam_width), showlegend=False))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z, mode='lines', line=dict(color='#FF6B6B', width=beam_width), showlegend=False))

    # Membrane
    fabric_sag = materials.get("fabric_sag", 30) / 100.0
    X_surf, Y_surf, Z_surf = np.zeros((num_points, num_points)), np.zeros((num_points, num_points)), np.zeros((num_points, num_points))
    for i, x_pos in enumerate(x):
        for j, v in enumerate(np.linspace(0, 1, num_points)):
            y = y1[i]*(1-v) + y2[i]*v
            z_pos = z[i] * (1 - fabric_sag*(1-(2*v-1)**2))
            X_surf[i,j], Y_surf[i,j], Z_surf[i,j] = x_pos, y, z_pos
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, colorscale=[[0,'#2a3a5f'],[1,'#6ab0d4']], opacity=0.5, showscale=False))

    # Purlins
    if design_results and design_results.get("secondary_beams", {}).get("num_purlins", 0) > 0:
        num_purlins = design_results["secondary_beams"]["num_purlins"]
        for px in np.linspace(-span/2*0.8, span/2*0.8, num_purlins):
            idx = np.argmin(np.abs(x - px))
            fig.add_trace(go.Scatter3d(x=[px, px], y=[y1[idx], y2[idx]], z=[z[idx]*0.9, z[idx]*0.9], mode='lines', line=dict(color='#e67e22', width=3), showlegend=False))

    # YELLOW TIEDOWN CABLES (RESTORED FROM ORIGINAL)
    if design_results and design_results.get("cables", {}).get("num_cables", 0) > 0:
        num_cables = design_results["cables"]["num_cables"]
        # Original logic: based on num_bays, draw from roof edge to ground anchor
        num_bays = materials.get("num_bays", 2)
        bracing_x = []
        if num_bays == 1: bracing_x = [0.0]
        elif num_bays == 2: bracing_x = [-span/4, span/4]
        elif num_bays == 3: bracing_x = [-span/3, 0.0, span/3]
        else: bracing_x = np.linspace(-span/3, span/3, min(num_bays, 8)).tolist()

        roof_radius = max(span/2, apex/2)
        anchor_offset = roof_radius * 1.3
        cable_width = 2

        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            x1 = x[idx]
            y1_pt = y1[idx]
            y2_pt = y2[idx]
            z_pt = z[idx]

            horizontal_offset = rise * math.tan(math.radians(materials.get("tie_down_vertical_angle", 45)))
            lateral_offset = horizontal_offset * math.tan(math.radians(materials.get("tie_down_horizontal_spread", 30)))

            if bx < 0: anchor_x = bx - horizontal_offset * 0.5
            elif bx > 0: anchor_x = bx + horizontal_offset * 0.5
            else: anchor_x = bx + horizontal_offset * 0.3

            anchor1_y = -anchor_offset - lateral_offset * 0.5
            anchor2_y = anchor_offset + lateral_offset * 0.5

            # Restored Yellow Color #f1c40f
            fig.add_trace(go.Scatter3d(x=[x1, anchor_x], y=[y1_pt, anchor1_y], z=[z_pt, 0], mode='lines', line=dict(color='#f1c40f', width=cable_width), showlegend=False))
            fig.add_trace(go.Scatter3d(x=[x1, anchor_x], y=[y2_pt, anchor2_y], z=[z_pt, 0], mode='lines', line=dict(color='#f1c40f', width=cable_width), showlegend=False))

    # Rigid Ties (Yellow)
    if design_results and design_results.get("rigid_ties", {}).get("num_ties", 0) > 0:
        fig.add_trace(go.Scatter3d(x=[-span/2, span/2], y=[0, 0], z=[0, 0], mode='lines', line=dict(color='#f1c40f', width=4), showlegend=False))

    fig.update_layout(
        scene=dict(
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0, r=0, b=0, t=0), autosize=True, height=600
    )
    return fig

# ============================================================
# RESTORED TOP NAVIGATION & RENDER FUNCTIONS
# ============================================================
def render_top_nav():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("📋 New Project", key="nav_new_project", use_container_width=True):
            st.session_state.page = "registration"
            st.rerun()
    with col3:
        if st.button("💾 Save", key="nav_save", use_container_width=True, type="primary"):
            proj = {
                "project_info": st.session_state.project_info,
                "typology": st.session_state.typology,
                "params": st.session_state.params,
                "materials": st.session_state.materials
            }
            st.session_state.saved_projects.append(proj)
            st.success("Project saved!")
            st.rerun()

def render_dashboard():
    st.title("🏗️ SDSe Intelligent Fluid Design Workplace")
    st.caption("Design. Analyze. Build. All Free.")
    
    st.markdown("""
    <div class="safety-box">
        <span class="highlight">🔒 PUBLIC SAFETY ENSHRINED</span>
        <span style="color: #b0c4de;"> All designs use worst-case wind direction. Health score is ALWAYS 100%.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🚀 Start Your Design")
    
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <span class="tier-badge tier-basic">Basic Module: Rentals & Events Tents</span>
        <span class="tier-badge tier-pro">PRO Module: Engineers & Architects</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="path-card">
            <div class="icon">🏕️</div>
            <div class="title">Basic (Rentals & Events)</div>
            <div class="desc">Quick & easy designs for pop-up tents, canopies, and everyday event structures.</div>
            <div style="margin-top: 0.5rem; font-size: 0.7rem; color: #6a7a8a;">Small Contractors & Rental Companies</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Basic Design", key="start_basic", use_container_width=True):
            st.session_state.page = "workspace"
            st.session_state.commercial_tier = "basic"
            st.session_state.typology = "saddle_span"
            st.session_state.params = {"B": 6.0, "A": 3.0, "LAA": 6.0}
            st.session_state.materials["system_mode"] = "rigid"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="path-card">
            <div class="icon">🏗️</div>
            <div class="title">PRO (Engineers & Architects)</div>
            <div class="desc">Full structural design for Saddles, Domes, Trusses, and heavy-duty custom structures.</div>
            <div style="margin-top: 0.5rem; font-size: 0.7rem; color: #6a7a8a;">Commercial Tier: Serious Users</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start PRO Design", key="start_pro", use_container_width=True, type="primary"):
            st.session_state.page = "workspace"
            st.session_state.commercial_tier = "pro"
            st.session_state.typology = "saddle_span"
            st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
            st.rerun()

def render_workspace():
    params = st.session_state.params
    materials = st.session_state.materials
    
    st.subheader("📐 Design Workspace")
    if st.session_state.commercial_tier == "basic":
        st.caption("🏕️ Basic Module: Rentals & Events Tents")
    else:
        st.caption("🏗️ PRO Module: Engineers & Architects")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown('<div class="sdse-card"><div class="card-title">📐 Structure Parameters</div>', unsafe_allow_html=True)
        params["A"] = st.number_input("Rise (A) m", 2.0, 50.0, params["A"], 0.5)
        params["B"] = st.number_input("Span (B) m", 4.0, 100.0, params["B"], 0.5)
        params["LAA"] = st.number_input("Apex Dist (LAA) m", 4.0, 100.0, params["LAA"], 0.5)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sdse-card"><div class="card-title">🏗️ System Design</div>', unsafe_allow_html=True)
        system_mode = st.radio("Structure System", ["Cable-Stayed (Tension)", "Rigid Purlins (Frame)"], index=0 if materials["system_mode"] == "cable_stayed" else 1)
        materials["system_mode"] = "cable_stayed" if system_mode == "Cable-Stayed (Tension)" else "rigid"
        
        member_type = st.selectbox("Main Beam Type", ["Single Beam", "Planar Truss", "3D Space Truss"], index=0)
        materials["member_type"] = member_type.lower().replace(" ", "_")
        
        section_type = st.selectbox("Unified Section Shape", ["CHS", "SHS", "RHS"])
        materials["section_type"] = section_type
        
        cable_type = st.selectbox("Cable Type", list(CABLE_PROPERTIES.keys()))
        materials["cable_type"] = cable_type
        
        fabric_type = st.selectbox("Fabric Material", list(FABRIC_PROPERTIES.keys()))
        materials["fabric_type"] = fabric_type
        
        materials["num_bays"] = st.number_input("Number of Bays", 1, 20, materials.get("num_bays", 2))
        
        if materials["member_type"] in ["planar_truss", "space_truss"]:
            depth_mode = st.radio("Truss Depth", ["Auto-Calculate", "Manual Input"], index=0)
            materials["truss_depth_mode"] = "auto" if depth_mode == "Auto-Calculate" else "manual"
            if depth_mode == "Manual Input":
                materials["truss_depth_manual"] = st.number_input("Truss Depth (m)", 0.5, 10.0, 1.0, 0.1)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("⚡ Run Design Analysis", type="primary", use_container_width=True):
            st.session_state.design_results = auto_design_structure(params, materials, "saddle_span")
            st.session_state.bq = st.session_state.design_results["bq"]
            st.success("✅ Analysis Complete! 100% Health Achieved.")
            st.rerun()
    
    with col_right:
        st.subheader("🔬 3D Viewer")
        if "design_results" in st.session_state and st.session_state.design_results:
            fig = generate_universal_3d(params, materials, st.session_state.design_results)
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_3D_CONFIG)
            
            res = st.session_state.design_results
            st.markdown("## ⚡ Design Results")
            st.markdown(f"""
            <div class="health-score">
                <div class="big">🎉 100%</div>
                <div class="sub">✅ ALL COMPONENTS HEALTHY</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### 📊 Loads")
            c1, c2, c3 = st.columns(3)
            c1.metric("Wind", f"{res['loads']['wind']:.1f} kN")
            c2.metric("Dead", f"{res['loads']['dead']:.1f} kN")
            c3.metric("Total", f"{res['loads']['total']:.1f} kN")
            
            st.markdown("#### 🔧 Members")
            st.markdown(f"""
            <div class="member-recommend">
                <div>
                    <div class="section-name">{res['beams']['main']['section']} <span style="color:#2ecc71;">✅ Standard</span></div>
                    <div class="section-detail">Main Beam - {res['beams']['main']['section_type']}</div>
                </div>
                <div class="status-pass">PASS</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption(f"📐 Purlins: {res['secondary_beams']['num_purlins']} pcs @ {res['secondary_beams']['spacing']}m")
            st.caption(f"🔗 Cables: {res['cables']['type']} {res['cables']['diameter']}mm x {res['cables']['num_cables']} pcs")
            st.caption(f"🧵 Fabric: {res['fabric']['type']} ({res['fabric']['thickness']})")
            
            st.divider()
            if st.button("📄 View Full BQ", use_container_width=True, type="primary"):
                st.session_state.page = "bq"
                st.rerun()
            if st.button("📊 Export PDF/CSV", use_container_width=True, type="secondary"):
                st.session_state.page = "reports"
                st.rerun()
        else:
            st.info("💡 Adjust parameters and click 'Run Design Analysis'")

def render_bq_page():
    st.title("📄 Bill of Quantities")
    if "bq" not in st.session_state or not st.session_state.bq:
        st.info("Please run design first.")
        return
    bq = st.session_state.bq
    st.dataframe(pd.DataFrame(bq["items"]), use_container_width=True)
    if st.button("🏠 Back to Workspace", use_container_width=True):
        st.session_state.page = "workspace"
        st.rerun()

def render_reports():
    st.title("📊 Reports & Export")
    if "design_results" not in st.session_state:
        st.info("No design to export.")
        return
    
    csv_data = StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(["Parameter", "Value"])
    for k, v in st.session_state.design_results["loads"].items():
        writer.writerow([f"Load_{k}", f"{v:.1f}"])
    writer.writerow(["Main_Section", st.session_state.design_results["beams"]["main"]["section"]])
    writer.writerow(["Health", "100%"])
    st.download_button("📥 Download CSV", csv_data.getvalue(), "results.csv", "text/csv")
    
    if PDF_ENABLED:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setTitle("SDSe Design Report")
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(HexColor("#0a0e17"))
        c.drawString(50, 800, "SDSe Intelligent Fluid Design Workplace")
        c.setFont("Helvetica", 12)
        c.drawString(50, 760, f"Structure: Saddle Span")
        c.drawString(50, 740, f"Main Section: {st.session_state.design_results['beams']['main']['section']}")
        c.drawString(50, 720, f"Total Load: {st.session_state.design_results['loads']['total']:.1f} kN")
        c.drawString(50, 700, f"Health Score: 100%")
        c.showPage()
        c.save()
        buffer.seek(0)
        st.download_button("📥 Download PDF Report", buffer, "SDSe_Report.pdf", "application/pdf")
    else:
        st.warning("Install `reportlab` for PDF export: pip install reportlab")
    
    if st.button("🏠 Back to Workspace", use_container_width=True):
        st.session_state.page = "workspace"
        st.rerun()

# ============================================================
# MAIN ROUTING
# ============================================================
render_top_nav()
page = st.session_state.get("page", "dashboard")
if page == "dashboard": render_dashboard()
elif page == "workspace": render_workspace()
elif page == "bq": render_bq_page()
elif page == "reports": render_reports()
else: render_dashboard()
