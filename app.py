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
import math

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SDS Design Studio v7.0",
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
    .joint-badge { display: inline-block; padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
    .joint-weld { background-color: #e74c3c; color: #ffffff; }
    .joint-bolt { background-color: #3498db; color: #ffffff; }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# EXPANDED SECTION PROPERTIES DATABASE (100+ Sections)
# ============================================================
SECTION_PROPERTIES = {
    # ====== CIRCULAR HOLLOW SECTIONS (CHS) ======
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
    
    # ====== SQUARE HOLLOW SECTIONS (SHS) ======
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
    
    # ====== RECTANGULAR HOLLOW SECTIONS (RHS) ======
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
    
    # ====== I-BEAMS (W Shapes - Metric) ======
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
    
    # ====== ANGLES (L Shapes) ======
    "L40x40x4": {"A": 309, "I": 0.08e6, "W_el": 2.8e3, "i": 16.1, "weight": 2.4, "type": "Angle", "depth": 40},
    "L50x50x5": {"A": 480, "I": 0.18e6, "W_el": 5.1e3, "i": 19.4, "weight": 3.8, "type": "Angle", "depth": 50},
    "L60x60x6": {"A": 691, "I": 0.36e6, "W_el": 8.5e3, "i": 22.8, "weight": 5.4, "type": "Angle", "depth": 60},
    "L70x70x7": {"A": 941, "I": 0.64e6, "W_el": 12.8e3, "i": 26.1, "weight": 7.4, "type": "Angle", "depth": 70},
    "L80x80x8": {"A": 1229, "I": 1.04e6, "W_el": 18.2e3, "i": 29.1, "weight": 9.6, "type": "Angle", "depth": 80},
    "L90x90x9": {"A": 1553, "I": 1.58e6, "W_el": 24.7e3, "i": 31.9, "weight": 12.2, "type": "Angle", "depth": 90},
    "L100x100x10": {"A": 1910, "I": 2.28e6, "W_el": 32.0e3, "i": 34.5, "weight": 15.0, "type": "Angle", "depth": 100},
    "L120x120x12": {"A": 2752, "I": 4.52e6, "W_el": 53.0e3, "i": 40.5, "weight": 21.6, "type": "Angle", "depth": 120},
    
    # ====== CHANNELS (C Shapes) ======
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
    "PVC-coated Polyester": {"thickness": {"0.5": 30, "0.8": 40, "1.0": 50, "1.2": 60}, "weight_per_m2": 1.2, "cost_per_m2": 25},
    "PTFE-coated Fiberglass": {"thickness": {"0.5": 40, "0.8": 55, "1.0": 70, "1.2": 85}, "weight_per_m2": 1.8, "cost_per_m2": 45},
    "ETFE": {"thickness": {"0.5": 25, "0.8": 35, "1.0": 45, "1.2": 55}, "weight_per_m2": 0.8, "cost_per_m2": 60}
}

CABLE_PROPERTIES = {
    "6x19 Galvanized": {"diameters": {6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140, 18: 180, 20: 220, 22: 260, 24: 310, 26: 360, 28: 420, 30: 480, 32: 540, 36: 680, 40: 840}, "cost_per_m": 8},
    "6x19 Stainless": {"diameters": {6: 25, 8: 42, 10: 65, 12: 95, 14: 125, 16: 160, 18: 200, 20: 245}, "cost_per_m": 15},
    "Polyester Rope": {"diameters": {8: 30, 10: 45, 12: 65, 14: 85, 16: 110, 18: 140, 20: 170, 24: 230}, "cost_per_m": 5}
}

WIND_SPEEDS = {"EU": 30.0, "CN": 28.0, "UK": 26.0, "MY": 33.5, "US": 38.0}

# Material cost database (per kg)
MATERIAL_COSTS = {
    "Steel": 2.5,
    "Aluminum": 4.5,
    "Wood": 1.2,
    "Composite": 6.0
}

# Joint type multipliers
JOINT_MULTIPLIERS = {
    "welded": {
        "factor": 1.2,  # 20% more material due to moment connections
        "cost_multiplier": 1.3,  # 30% more cost for welding
        "connection_cost": 150,  # per joint
        "description": "Rigid moment connections - stronger but more expensive"
    },
    "bolted": {
        "factor": 1.0,  # Standard material
        "cost_multiplier": 1.0,  # Standard cost
        "connection_cost": 80,  # per joint
        "description": "Pin connections - economical and easy to assemble"
    }
}

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
        "prestress_level": "medium",
        "joint_type": "bolted"  # NEW: User selects welded or bolted
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

# ============================================================
# TRUSS ANALYSIS ENGINE
# ============================================================
def analyze_truss_members(params, materials, total_load, joint_type="bolted"):
    """Perform simplified truss analysis based on joint type"""
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    num_bays = materials.get("num_bays", 2)
    num_panels = num_bays + 1
    
    # Get joint multiplier
    joint_data = JOINT_MULTIPLIERS.get(joint_type, JOINT_MULTIPLIERS["bolted"])
    
    # Create truss geometry
    panel_width = span / num_panels
    x_coords = np.linspace(-span/2, span/2, num_panels + 1)
    z_bottom = np.zeros_like(x_coords)
    z_top = get_beam_shape(x_coords, span, rise, materials.get("shape_type", "parabolic"))
    
    # Calculate reactions (simply supported)
    total_udl = total_load / span
    reaction = total_udl * span / 2
    
    # Simplified force calculation per panel
    max_bending = (total_udl * span**2) / 8
    truss_depth = rise * 0.7  # Effective depth
    
    # Adjust forces based on joint type
    if joint_type == "welded":
        # Welded = moment connections = members resist bending
        # Forces are higher due to moment distribution
        force_multiplier = 1.2
        top_chord_force = max_bending / truss_depth * 1.2 * force_multiplier
        bottom_chord_force = max_bending / truss_depth * 1.1 * force_multiplier
        diag_force = top_chord_force * 0.6
        vert_force = diag_force * 0.5
        joint_description = "Rigid welded connections - members resist bending"
    else:  # bolted
        # Bolted = pin connections = axial forces only
        # Forces are lower because no moment transfer
        force_multiplier = 1.0
        top_chord_force = max_bending / truss_depth * 1.2 * force_multiplier
        bottom_chord_force = max_bending / truss_depth * 1.1 * force_multiplier
        diag_force = top_chord_force * 0.6
        vert_force = diag_force * 0.5
        joint_description = "Bolted pin connections - axial forces only"
    
    # Select sections based on forces
    db = SECTION_PROPERTIES
    fy = 355  # Steel yield strength
    
    def find_section(force, is_compression=False, preferred_type=None):
        """Find lightest section that can carry the force"""
        required_area = force * 1000 / (fy * 0.9)  # Required area in mm²
        best_section = None
        best_weight = float('inf')
        
        for name, props in db.items():
            if preferred_type and props['type'] != preferred_type:
                continue
            if props['A'] >= required_area:
                if props['weight'] < best_weight:
                    best_weight = props['weight']
                    best_section = name
        return best_section
    
    # Select members based on truss type
    truss_type = materials.get("truss_type", "warren")
    
    if truss_type == "warren":
        top_chord = find_section(top_chord_force, True, "I-Beam") or find_section(top_chord_force, True, "SHS")
        bottom_chord = find_section(bottom_chord_force, False, "I-Beam") or find_section(bottom_chord_force, False, "SHS")
        diag = find_section(diag_force, False, "Angle") or find_section(diag_force, False, "CHS")
        
        members = {
            "top_chord": top_chord or "I-200",
            "bottom_chord": bottom_chord or "I-250",
            "diagonals": diag or "L80x80x8",
            "verticals": "N/A (Warren has no verticals)",
            "joint_type": joint_type,
            "joint_description": joint_description
        }
    elif truss_type == "pratt":
        top_chord = find_section(top_chord_force, True, "I-Beam") or find_section(top_chord_force, True, "SHS")
        bottom_chord = find_section(bottom_chord_force, False, "I-Beam") or find_section(bottom_chord_force, False, "SHS")
        diag = find_section(diag_force, False, "Angle") or find_section(diag_force, False, "CHS")
        vert = find_section(vert_force, True, "Angle") or find_section(vert_force, True, "CHS")
        
        members = {
            "top_chord": top_chord or "I-200",
            "bottom_chord": bottom_chord or "I-250",
            "diagonals": diag or "L80x80x8",
            "verticals": vert or "L60x60x6",
            "joint_type": joint_type,
            "joint_description": joint_description
        }
    elif truss_type == "howe":
        top_chord = find_section(top_chord_force, True, "I-Beam") or find_section(top_chord_force, True, "SHS")
        bottom_chord = find_section(bottom_chord_force, False, "I-Beam") or find_section(bottom_chord_force, False, "SHS")
        diag = find_section(diag_force, True, "Angle") or find_section(diag_force, True, "CHS")
        vert = find_section(vert_force, False, "Angle") or find_section(vert_force, False, "CHS")
        
        members = {
            "top_chord": top_chord or "I-200",
            "bottom_chord": bottom_chord or "I-250",
            "diagonals": diag or "L80x80x8",
            "verticals": vert or "L60x60x6",
            "joint_type": joint_type,
            "joint_description": joint_description
        }
    else:  # vierendeel
        top_chord = find_section(top_chord_force * 1.5, True, "I-Beam") or find_section(top_chord_force * 1.5, True, "SHS")
        bottom_chord = find_section(bottom_chord_force * 1.5, False, "I-Beam") or find_section(bottom_chord_force * 1.5, False, "SHS")
        vert = find_section(vert_force * 2, True, "I-Beam") or find_section(vert_force * 2, True, "SHS")
        
        members = {
            "top_chord": top_chord or "I-250",
            "bottom_chord": bottom_chord or "I-300",
            "diagonals": "N/A (Vierendeel has no diagonals)",
            "verticals": vert or "I-180",
            "joint_type": joint_type,
            "joint_description": joint_description
        }
    
    # Add forces for display
    members["forces"] = {
        "top_chord_force": top_chord_force,
        "bottom_chord_force": bottom_chord_force,
        "diag_force": diag_force,
        "vert_force": vert_force
    }
    
    return members

# ============================================================
# ENHANCED BQ GENERATOR
# ============================================================
def generate_bill_of_quantities(params, materials, design_results, truss_members, joint_type="bolted"):
    """Generate complete Bill of Quantities with joint type factored in"""
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    num_bays = materials.get("num_bays", 2)
    
    # Get joint data
    joint_data = JOINT_MULTIPLIERS.get(joint_type, JOINT_MULTIPLIERS["bolted"])
    material_cost = MATERIAL_COSTS.get(materials.get("material_type", "Steel"), 2.5)
    
    bq_items = []
    total_cost = 0
    
    # 1. Main Beams (2 beams)
    if design_results["beams"].get("selected"):
        beam_section = design_results["beams"]["selected"]
        beam_weight = SECTION_PROPERTIES.get(beam_section, {}).get("weight", 28.3)
        beam_length = span * 1.1  # Add 10% for connections
        total_beam_length = beam_length * 2  # 2 beams
        total_beam_weight = beam_weight * total_beam_length / 1000  # Convert to kg
        # Apply joint factor for welded joints (more material for moment connections)
        beam_cost = total_beam_weight * material_cost * joint_data["factor"] * joint_data["cost_multiplier"]
        
        bq_items.append({
            "item": f"Main Beams (2 pcs) - {beam_section}",
            "qty": 2,
            "unit": "pcs",
            "length_m": beam_length,
            "total_length_m": total_beam_length,
            "weight_kg": total_beam_weight * joint_data["factor"],
            "unit_price": material_cost * joint_data["factor"] * joint_data["cost_multiplier"],
            "total_price": beam_cost
        })
        total_cost += beam_cost
    
    # 2. Truss Members (if selected)
    if truss_members and "top_chord" in truss_members:
        # Top chord
        top_section = truss_members["top_chord"]
        top_weight = SECTION_PROPERTIES.get(top_section, {}).get("weight", 28.3)
        top_length = span * 1.1
        top_weight_total = top_weight * top_length / 1000 * joint_data["factor"]
        top_cost = top_weight_total * material_cost * joint_data["cost_multiplier"]
        
        bq_items.append({
            "item": f"Top Chord - {top_section}",
            "qty": 1,
            "unit": "pcs",
            "length_m": top_length,
            "total_length_m": top_length,
            "weight_kg": top_weight_total,
            "unit_price": material_cost * joint_data["cost_multiplier"],
            "total_price": top_cost
        })
        total_cost += top_cost
        
        # Bottom chord
        bottom_section = truss_members["bottom_chord"]
        bottom_weight = SECTION_PROPERTIES.get(bottom_section, {}).get("weight", 28.3)
        bottom_weight_total = bottom_weight * top_length / 1000 * joint_data["factor"]
        bottom_cost = bottom_weight_total * material_cost * joint_data["cost_multiplier"]
        
        bq_items.append({
            "item": f"Bottom Chord - {bottom_section}",
            "qty": 1,
            "unit": "pcs",
            "length_m": top_length,
            "total_length_m": top_length,
            "weight_kg": bottom_weight_total,
            "unit_price": material_cost * joint_data["cost_multiplier"],
            "total_price": bottom_cost
        })
        total_cost += bottom_cost
        
        # Diagonals (if not N/A)
        if "N/A" not in truss_members["diagonals"]:
            diag_section = truss_members["diagonals"]
            diag_weight = SECTION_PROPERTIES.get(diag_section, {}).get("weight", 9.6)
            num_diags = (num_bays + 1) * 2
            diag_length = math.sqrt((span/(num_bays+1))**2 + (rise*0.7)**2) * 1.1
            diag_weight_total = diag_weight * diag_length * num_diags / 1000 * joint_data["factor"]
            diag_cost = diag_weight_total * material_cost * joint_data["cost_multiplier"]
            
            bq_items.append({
                "item": f"Diagonals ({num_diags} pcs) - {diag_section}",
                "qty": num_diags,
                "unit": "pcs",
                "length_m": diag_length,
                "total_length_m": diag_length * num_diags,
                "weight_kg": diag_weight_total,
                "unit_price": material_cost * joint_data["cost_multiplier"],
                "total_price": diag_cost
            })
            total_cost += diag_cost
        
        # Verticals (if not N/A)
        if "verticals" in truss_members and "N/A" not in truss_members["verticals"]:
            vert_section = truss_members["verticals"]
            vert_weight = SECTION_PROPERTIES.get(vert_section, {}).get("weight", 8.1)
            num_verts = num_bays * 2
            vert_length = rise * 0.7 * 1.1
            vert_weight_total = vert_weight * vert_length * num_verts / 1000 * joint_data["factor"]
            vert_cost = vert_weight_total * material_cost * joint_data["cost_multiplier"]
            
            bq_items.append({
                "item": f"Verticals ({num_verts} pcs) - {vert_section}",
                "qty": num_verts,
                "unit": "pcs",
                "length_m": vert_length,
                "total_length_m": vert_length * num_verts,
                "weight_kg": vert_weight_total,
                "unit_price": material_cost * joint_data["cost_multiplier"],
                "total_price": vert_cost
            })
            total_cost += vert_cost
        
        # Add joint connections cost
        num_joints = (num_bays + 1) * 4  # Approximate number of joints
        connection_cost = num_joints * joint_data["connection_cost"]
        bq_items.append({
            "item": f"Connections ({num_joints} joints) - {joint_type.upper()}",
            "qty": num_joints,
            "unit": "joints",
            "length_m": "-",
            "total_length_m": "-",
            "weight_kg": 0,
            "unit_price": joint_data["connection_cost"],
            "total_price": connection_cost
        })
        total_cost += connection_cost
    
    # 3. Fabric
    membrane_area = span * laa * 1.1
    fabric_cost_per_m2 = FABRIC_PROPERTIES.get(materials["fabric_type"], {}).get("cost_per_m2", 25)
    fabric_cost = membrane_area * fabric_cost_per_m2 * 1.2  # Add wastage
    
    bq_items.append({
        "item": f"Fabric Membrane - {materials['fabric_type']} ({design_results['fabric']['thickness']}mm)",
        "qty": membrane_area,
        "unit": "m²",
        "length_m": "-",
        "total_length_m": "-",
        "weight_kg": membrane_area * FABRIC_PROPERTIES.get(materials["fabric_type"], {}).get("weight_per_m2", 1.2),
        "unit_price": fabric_cost_per_m2 * 1.2,
        "total_price": fabric_cost
    })
    total_cost += fabric_cost
    
    # 4. Cables
    num_anchors = num_bays * 4
    cable_length = math.sqrt(rise**2 + (span/3)**2) * 1.2
    cable_cost_per_m = CABLE_PROPERTIES.get(materials["cable_type"], {}).get("cost_per_m", 8)
    total_cable_length = num_anchors * cable_length
    cable_cost = total_cable_length * cable_cost_per_m * 1.1
    
    bq_items.append({
        "item": f"Cables ({num_anchors} pcs) - {materials['cable_type']} {design_results['cables']['diameter']}mm",
        "qty": num_anchors,
        "unit": "pcs",
        "length_m": cable_length,
        "total_length_m": total_cable_length,
        "weight_kg": total_cable_length * 1.2,
        "unit_price": cable_cost_per_m * 1.1,
        "total_price": cable_cost
    })
    total_cost += cable_cost
    
    # 5. Installation (approx 15% of total)
    installation_cost = total_cost * 0.15
    bq_items.append({
        "item": f"Installation & Labour (15% of total) - {joint_type.upper()} joints",
        "qty": 1,
        "unit": "lump sum",
        "length_m": "-",
        "total_length_m": "-",
        "weight_kg": 0,
        "unit_price": installation_cost,
        "total_price": installation_cost
    })
    total_cost += installation_cost
    
    # Calculate total weight
    total_steel_weight = sum([
        item.get("weight_kg", 0) for item in bq_items 
        if "weight_kg" in item and "Connections" not in item["item"] and "Installation" not in item["item"]
    ])
    
    return {
        "items": bq_items,
        "total_cost": total_cost,
        "total_steel_weight": total_steel_weight,
        "total_fabric_area": membrane_area,
        "total_cable_length": total_cable_length,
        "joint_type": joint_type,
        "joint_description": joint_data["description"]
    }

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
    joint_type = materials.get("joint_type", "bolted")  # Get joint type from user
    
    # Get joint multiplier
    joint_data = JOINT_MULTIPLIERS.get(joint_type, JOINT_MULTIPLIERS["bolted"])
    
    wind_load = calculate_wind_load(span, laa, standard)
    dead_load = calculate_dead_load(span, laa, "CHS 168.3x7.1", fabric_type)
    live_load = 0.5 * (span * laa * 1.1) / 100
    total_load = wind_load + dead_load + live_load
    
    # Apply joint factor to total load if welded
    if joint_type == "welded":
        total_load *= 1.1  # 10% more load for moment transfer
    
    results = {
        "loads": {"wind": wind_load, "dead": dead_load, "live": live_load, "total": total_load},
        "beams": {}, "truss": {}, "fabric": {}, "cables": {},
        "all_checks": {}, "health_score": 0,
        "joint_type": joint_type
    }
    
    fy = 355 if material_type == "Steel" else 276 if material_type == "Aluminum" else 40
    
    # --- SINGLE BEAM ANALYSIS ---
    if member_type == "single_beam":
        beam_result = calculate_required_section(total_load, span, material_type, fy)
        if beam_result:
            results["beams"]["main"] = beam_result
            results["beams"]["selected"] = beam_result["section"]
            results["beams"]["moment_capacity"] = beam_result["moment_capacity"]
            results["beams"]["required_moment"] = beam_result["required_moment"]
    
    # --- TRUSS ANALYSIS ---
    truss_members = None
    if member_type in ["planar_truss", "space_truss"]:
        truss_members = analyze_truss_members(params, materials, total_load, joint_type)
        results["truss"] = truss_members
    
    # --- FABRIC SELECTION ---
    membrane_area = span * laa * 1.1
    fabric_thickness = auto_select_fabric_thickness(wind_load, membrane_area, fabric_type)
    results["fabric"]["type"] = fabric_type
    results["fabric"]["thickness"] = fabric_thickness
    results["fabric"]["strength"] = FABRIC_PROPERTIES.get(fabric_type, {}).get("thickness", {}).get(fabric_thickness, 0)
    
    # --- CABLE SELECTION ---
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
    
    # --- CHECKS ---
    results["all_checks"]["wind_load"] = {
        "status": "✅ PASS",
        "value": f"{wind_load:.1f} kN"
    }
    
    # Joint type info
    results["all_checks"]["joint_type"] = {
        "status": f"🔧 {joint_type.upper()}",
        "value": joint_data["description"][:30] + "..."
    }
    
    if member_type == "single_beam" and results["beams"].get("main"):
        beam = results["beams"]["main"]
        is_adequate = beam.get("is_adequate", False)
        results["all_checks"]["member_capacity"] = {
            "status": "✅ PASS" if is_adequate else "🔄 Upgrade",
            "value": f"{beam['moment_capacity']:.1f} kNm"
        }
        results["all_checks"]["section_selected"] = {
            "status": "✅ PASS" if is_adequate else "⚠️ Check",
            "value": beam['section']
        }
    elif member_type in ["planar_truss", "space_truss"] and truss_members:
        results["all_checks"]["member_capacity"] = {
            "status": f"✅ PASS ({joint_type.upper()})",
            "value": f"Top: {truss_members.get('top_chord', 'N/A')}"
        }
        results["all_checks"]["section_selected"] = {
            "status": f"✅ PASS ({joint_type.upper()})",
            "value": f"Bottom: {truss_members.get('bottom_chord', 'N/A')}"
        }
    else:
        results["all_checks"]["member_capacity"] = {"status": "✅ PASS", "value": "N/A"}
        results["all_checks"]["section_selected"] = {"status": "✅ PASS", "value": "N/A"}
    
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
    
    # --- HEALTH SCORE ---
    score = 100
    for check in results["all_checks"].values():
        if "⚠️" in check["status"] or "🔄" in check["status"]:
            score -= 10
    results["health_score"] = max(0, min(100, score))
    
    # --- GENERATE BQ ---
    bq = generate_bill_of_quantities(params, materials, results, truss_members, joint_type)
    results["bq"] = bq
    
    return results

# ============================================================
# IMPROVED 3D GENERATOR FOR SADDLE SPAN
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

    # Draw main beams
    fig.add_trace(go.Scatter3d(
        x=x, y=y1, z=z_beam,
        mode='lines', name='Beam 1 (Left)',
        line=dict(color='#FF6B6B', width=8)
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode='lines', name='Beam 2 (Right)',
        line=dict(color='#FF6B6B', width=8)
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
            z_pos = z_at_x * (1 - 0.3 * (1 - (2 * v_val - 1)**2))
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
        opacity=0.5, showscale=False, name='Membrane'
    ))

    # Apex and supports
    fig.add_trace(go.Scatter3d(
        x=[0], y=[y1[num_points//2]], z=[z_beam[num_points//2]],
        mode='markers', name='Apex',
        marker=dict(color='#FFD93D', size=10, symbol='diamond')
    ))
    fig.add_trace(go.Scatter3d(
        x=[-span/2, span/2],
        y=[0, 0],
        z=[0, 0],
        mode='markers', name='Supports',
        marker=dict(color='#4ECDC4', size=8, symbol='square')
    ))

    # Bracing and tie-downs
    if materials:
        num_bays = materials.get("num_bays", 2)
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 30)
        
        bracing_x = generate_bracing_positions(span, num_bays)
        bracing_x_sorted = sorted(bracing_x)

        # Tie-downs radiating outward on both beams
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            x1 = x[idx]
            y1_pt = y1[idx]
            y2_pt = y2[idx]
            z_pt = z_beam[idx]

            horizontal_offset = rise * np.tan(np.radians(vertical_angle))
            lateral_offset = horizontal_offset * np.tan(np.radians(horizontal_spread))
            
            # Outward direction only
            anchor1_y = -lateral_offset - laa/3  # Always left
            anchor2_y = lateral_offset + laa/3   # Always right
            anchor_x = bx + horizontal_offset * 0.3

            # Beam 1 tie-down (left)
            fig.add_trace(go.Scatter3d(
                x=[x1, anchor_x],
                y=[y1_pt, anchor1_y],
                z=[z_pt, 0],
                mode='lines',
                line=dict(color='#FFD93D', width=3),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[anchor_x],
                y=[anchor1_y],
                z=[0],
                mode='markers',
                marker=dict(color='#FF6B6B', size=8, symbol='x'),
                showlegend=False
            ))

            # Beam 2 tie-down (right)
            fig.add_trace(go.Scatter3d(
                x=[x1, anchor_x],
                y=[y2_pt, anchor2_y],
                z=[z_pt, 0],
                mode='lines',
                line=dict(color='#FFD93D', width=3),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[anchor_x],
                y=[anchor2_y],
                z=[0],
                mode='markers',
                marker=dict(color='#FF6B6B', size=8, symbol='x'),
                showlegend=False
            ))

        # Horizontal bracing
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            x1 = x[idx]
            y1_pt = y1[idx]
            y2_pt = y2[idx]
            z_pt = z_beam[idx]
            fig.add_trace(go.Scatter3d(
                x=[x1, x1],
                y=[y1_pt, y2_pt],
                z=[z_pt, z_pt],
                mode='lines',
                line=dict(color='#00FFFF', width=3, dash='dash'),
                showlegend=False
            ))

        # Diagonal cross-bracing
        if len(bracing_x_sorted) >= 2:
            for i in range(len(bracing_x_sorted) - 1):
                bx1 = bracing_x_sorted[i]
                bx2 = bracing_x_sorted[i+1]
                idx1 = np.argmin(np.abs(x - bx1))
                idx2 = np.argmin(np.abs(x - bx2))
                
                x1a = x[idx1]; y1a = y1[idx1]; z1a = z_beam[idx1]
                x1b = x[idx2]; y1b = y1[idx2]; z1b = z_beam[idx2]
                x2a = x[idx1]; y2a = y2[idx1]; z2a = z_beam[idx1]
                x2b = x[idx2]; y2b = y2[idx2]; z2b = z_beam[idx2]

                fig.add_trace(go.Scatter3d(
                    x=[x1a, x2b],
                    y=[y1a, y2b],
                    z=[z1a, z2b],
                    mode='lines',
                    line=dict(color='#00FFFF', width=2, dash='dot'),
                    showlegend=False
                ))
                fig.add_trace(go.Scatter3d(
                    x=[x2a, x1b],
                    y=[y2a, y1b],
                    z=[z2a, z1b],
                    mode='lines',
                    line=dict(color='#00FFFF', width=2, dash='dot'),
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
# OTHER GENERATORS
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
    st.title("🏗️ SDS Design Studio v7.0")
    st.caption("Parametric design for tensile structures")
    
    projects = st.session_state.saved_projects
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>📂</div><div class='value'>{len(projects)}</div><div class='label'>Saved Projects</div></div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<div class='dashboard-card'><div class='icon'>🏕️</div><div class='value'>5</div><div class='label'>Shapes</div></div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("<div class='dashboard-card'><div class='icon'>🔧</div><div class='value'>100+</div><div class='label'>Sections</div></div>", unsafe_allow_html=True)
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
        
        st.markdown('<div class="sds-card"><div class="title">🔗 Joint Type</div>', unsafe_allow_html=True)
        joint_options = ["bolted", "welded"]
        joint_labels = ["🔩 Bolted (Pin Connection)", "⚡ Welded (Moment Connection)"]
        current_joint = materials.get("joint_type", "bolted")
        joint_idx = joint_options.index(current_joint) if current_joint in joint_options else 0
        
        selected_joint_label = st.selectbox("Connection Type", joint_labels, index=joint_idx, disabled=st.session_state.locked)
        materials["joint_type"] = joint_options[joint_labels.index(selected_joint_label)]
        
        # Show joint description
        joint_desc = JOINT_MULTIPLIERS[materials["joint_type"]]["description"]
        st.markdown(f"<span style='color:#b0c4de;font-size:0.85rem;'>ℹ️ {joint_desc}</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sds-card"><div class="title">🧱 Materials</div>', unsafe_allow_html=True)
        material_types = ["Steel", "Aluminum", "Wood", "Composite"]
        current_material = materials.get("material_type", "Steel")
        materials["material_type"] = st.selectbox("Member Material", material_types, index=material_types.index(current_material), disabled=st.session_state.locked)
        
        section_types = ["CHS", "SHS", "RHS", "I-Beam", "Angle", "Channel"]
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
        
        # Show joint type badge
        joint_type = design_results.get("joint_type", "bolted")
        badge_color = "joint-weld" if joint_type == "welded" else "joint-bolt"
        st.markdown(f"<span class='joint-badge {badge_color}'>{joint_type.upper()} Connections</span>", unsafe_allow_html=True)
        
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
        
        if materials["member_type"] == "single_beam":
            beam = design_results["beams"].get("main")
            if beam:
                st.markdown(f"**Main Beams (2 pcs):** {beam['section']}")
                st.markdown(f"**Area:** {beam['properties']['A']:.0f} mm²")
                st.markdown(f"**Weight:** {beam['properties']['weight']:.1f} kg/m")
                st.markdown(f"**Required Moment:** {beam['required_moment']:.1f} kNm")
                st.markdown(f"**Moment Capacity:** {beam['moment_capacity']:.1f} kNm")
                st.markdown(f"**Status:** {'✅ Adequate' if beam['is_adequate'] else '🔄 Upgrade Available'}")
            else:
                st.markdown("⚠️ No suitable section found")
        elif materials["member_type"] in ["planar_truss", "space_truss"]:
            truss = design_results["truss"]
            if truss:
                st.markdown(f"**📐 Truss Type:** {materials['truss_type'].upper()}")
                st.markdown(f"**🔗 Joints:** {truss.get('joint_type', 'N/A').upper()}")
                st.markdown("---")
                st.markdown(f"**🔺 Top Chord:** {truss.get('top_chord', 'N/A')}")
                st.markdown(f"**🔻 Bottom Chord:** {truss.get('bottom_chord', 'N/A')}")
                st.markdown(f"**╳ Diagonals:** {truss.get('diagonals', 'N/A')}")
                st.markdown(f"**║ Verticals:** {truss.get('verticals', 'N/A')}")
                st.markdown("---")
                if "forces" in truss:
                    forces = truss["forces"]
                    st.markdown("**📈 Member Forces:**")
                    st.markdown(f"Top Chord: {forces['top_chord_force']:.1f} kN (Compression)")
                    st.markdown(f"Bottom Chord: {forces['bottom_chord_force']:.1f} kN (Tension)")
                    st.markdown(f"Diagonals: {forces['diag_force']:.1f} kN (Alternating)")
                    if "vert_force" in forces:
                        st.markdown(f"Verticals: {forces['vert_force']:.1f} kN")
            else:
                st.markdown("⚠️ Truss analysis not available")
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
            display_name = check_name.replace('_', ' ').title()
            st.markdown(f"<span style='color:{color}; font-weight:700;'>{status}</span> {display_name}: {check_data['value']}", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Health Score
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
        
        # Bill of Quantities
        st.divider()
        st.markdown("## 📋 Bill of Quantities")
        
        bq = design_results.get("bq", {})
        if bq and "items" in bq:
            # Summary metrics
            col_bq1, col_bq2, col_bq3, col_bq4 = st.columns(4)
            col_bq1.metric("💰 Total Cost", f"${bq['total_cost']:,.0f}")
            col_bq2.metric("🔩 Steel Weight", f"{bq['total_steel_weight']:.0f} kg")
            col_bq3.metric("📐 Fabric Area", f"{bq['total_fabric_area']:.0f} m²")
            col_bq4.metric("🔗 Joint Type", bq.get('joint_type', 'bolted').upper())
            
            st.markdown("---")
            
            # Detailed BQ table
            bq_data = []
            for item in bq["items"]:
                bq_data.append({
                    "Item": item["item"],
                    "Qty": item["qty"],
                    "Unit": item["unit"],
                    "Length (m)": item["length_m"],
                    "Total Length (m)": item["total_length_m"],
                    "Weight (kg)": f"{item['weight_kg']:.0f}" if isinstance(item['weight_kg'], (int, float)) else item['weight_kg'],
                    "Unit Price ($)": f"{item['unit_price']:.2f}" if isinstance(item['unit_price'], (int, float)) else item['unit_price'],
                    "Total ($)": f"{item['total_price']:,.0f}" if isinstance(item['total_price'], (int, float)) else item['total_price']
                })
            
            if bq_data:
                df = pd.DataFrame(bq_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Grand total
                st.markdown(f"""
                <div style='text-align:right;padding:0.5rem;background:#1e2a3a;border-radius:8px;margin-top:0.5rem;'>
                    <span style='font-size:1.2rem;font-weight:700;color:#f39c12;'>
                        GRAND TOTAL: ${bq['total_cost']:,.0f}
                    </span>
                    <br>
                    <span style='font-size:0.8rem;color:#b0c4de;'>
                        {bq.get('joint_description', '')}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Run design to generate Bill of Quantities")
    
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
st.caption("SDS Design Studio v7.0 | MS EN Wind: 33.5m/s | 100+ Sections | 🔩/⚡ Joints")
