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
    page_title="SDS Design Studio - International Standards",
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
# INTERNATIONAL STANDARDS - MATERIAL PROPERTIES
# ============================================================

# ===== EUROCODE (EU) =====
EU_STEEL_GRADES = {
    "S235 (EN 10025)": {"fy": 235, "fu": 360, "E": 210000, "density": 7850, "standard": "EU"},
    "S275 (EN 10025)": {"fy": 275, "fu": 430, "E": 210000, "density": 7850, "standard": "EU"},
    "S355 (EN 10025)": {"fy": 355, "fu": 490, "E": 210000, "density": 7850, "standard": "EU"},
    "S420 (EN 10025)": {"fy": 420, "fu": 520, "E": 210000, "density": 7850, "standard": "EU"},
    "S460 (EN 10025)": {"fy": 460, "fu": 550, "E": 210000, "density": 7850, "standard": "EU"}
}

# ===== CHINA (CN) =====
CN_STEEL_GRADES = {
    "Q235 (GB/T 700)": {"fy": 235, "fu": 375, "E": 206000, "density": 7850, "standard": "CN"},
    "Q345 (GB/T 1591)": {"fy": 345, "fu": 470, "E": 206000, "density": 7850, "standard": "CN"},
    "Q390 (GB/T 1591)": {"fy": 390, "fu": 490, "E": 206000, "density": 7850, "standard": "CN"},
    "Q420 (GB/T 1591)": {"fy": 420, "fu": 520, "E": 206000, "density": 7850, "standard": "CN"},
    "Q460 (GB/T 1591)": {"fy": 460, "fu": 550, "E": 206000, "density": 7850, "standard": "CN"}
}

# ===== BRITISH (UK) =====
UK_STEEL_GRADES = {
    "BS 43A (BS 4360)": {"fy": 275, "fu": 430, "E": 205000, "density": 7850, "standard": "UK"},
    "BS 50B (BS 4360)": {"fy": 355, "fu": 490, "E": 205000, "density": 7850, "standard": "UK"},
    "BS 50C (BS 4360)": {"fy": 355, "fu": 490, "E": 205000, "density": 7850, "standard": "UK"},
    "BS 55C (BS 4360)": {"fy": 460, "fu": 550, "E": 205000, "density": 7850, "standard": "UK"},
    "BS 55E (BS 4360)": {"fy": 460, "fu": 550, "E": 205000, "density": 7850, "standard": "UK"}
}

# ===== MALAYSIA (MY) =====
MY_STEEL_GRADES = {
    "S275 (MS EN 10025)": {"fy": 275, "fu": 430, "E": 210000, "density": 7850, "standard": "MY"},
    "S355 (MS EN 10025)": {"fy": 355, "fu": 490, "E": 210000, "density": 7850, "standard": "MY"},
    "S460 (MS EN 10025)": {"fy": 460, "fu": 550, "E": 210000, "density": 7850, "standard": "MY"},
    "S550 (MS EN 10025)": {"fy": 550, "fu": 620, "E": 210000, "density": 7850, "standard": "MY"}
}

# ===== USA (US) =====
US_STEEL_GRADES = {
    "A36 (ASTM A36)": {"fy": 250, "fu": 400, "E": 200000, "density": 7850, "standard": "US"},
    "A572 Gr50 (ASTM A572)": {"fy": 345, "fu": 450, "E": 200000, "density": 7850, "standard": "US"},
    "A992 (ASTM A992)": {"fy": 345, "fu": 450, "E": 200000, "density": 7850, "standard": "US"},
    "A913 Gr65 (ASTM A913)": {"fy": 450, "fu": 550, "E": 200000, "density": 7850, "standard": "US"},
    "A514 (ASTM A514)": {"fy": 690, "fu": 760, "E": 200000, "density": 7850, "standard": "US"}
}

# Combine all steel grades
ALL_STEEL_GRADES = {}
ALL_STEEL_GRADES.update(EU_STEEL_GRADES)
ALL_STEEL_GRADES.update(CN_STEEL_GRADES)
ALL_STEEL_GRADES.update(UK_STEEL_GRADES)
ALL_STEEL_GRADES.update(MY_STEEL_GRADES)
ALL_STEEL_GRADES.update(US_STEEL_GRADES)

# ===== WIND STANDARDS =====
EU_WIND_ZONES = {
    "Zone 1": {"basic_wind_speed": 26.0, "description": "Inland areas"},
    "Zone 2": {"basic_wind_speed": 30.0, "description": "Coastal areas"},
    "Zone 3": {"basic_wind_speed": 35.0, "description": "Mountainous regions"},
    "Zone 4": {"basic_wind_speed": 40.0, "description": "Exposed coastal"}
}

CN_WIND_ZONES = {
    "Zone I": {"basic_wind_speed": 28.0, "description": "Inland, low wind"},
    "Zone II": {"basic_wind_speed": 32.0, "description": "Inland, moderate wind"},
    "Zone III": {"basic_wind_speed": 35.0, "description": "Coastal, high wind"},
    "Zone IV": {"basic_wind_speed": 40.0, "description": "Coastal, very high wind"},
    "Zone V": {"basic_wind_speed": 45.0, "description": "Special coastal regions"}
}

UK_WIND_ZONES = {
    "Zone 1": {"basic_wind_speed": 26.0, "description": "Inland low"},
    "Zone 2": {"basic_wind_speed": 30.0, "description": "Inland moderate"},
    "Zone 3": {"basic_wind_speed": 34.0, "description": "Coastal moderate"},
    "Zone 4": {"basic_wind_speed": 38.0, "description": "Coastal high"},
    "Zone 5": {"basic_wind_speed": 42.0, "description": "Exposed coastal"}
}

MY_WIND_ZONES = {
    "Zone 1": {"basic_wind_speed": 32.6, "description": "Less than 32.6 m/s"},
    "Zone 2": {"basic_wind_speed": 37.2, "description": "32.6 - 37.2 m/s"},
    "Zone 3": {"basic_wind_speed": 41.8, "description": "37.2 - 41.8 m/s"},
    "Zone 4": {"basic_wind_speed": 46.5, "description": "41.8 - 46.5 m/s"},
    "Coastal": {"basic_wind_speed": 55.0, "description": "Coastal areas"}
}

US_WIND_ZONES = {
    "Zone 1": {"basic_wind_speed": 38.0, "description": "Inland low"},
    "Zone 2": {"basic_wind_speed": 42.0, "description": "Inland moderate"},
    "Zone 3": {"basic_wind_speed": 46.0, "description": "Coastal moderate"},
    "Zone 4": {"basic_wind_speed": 50.0, "description": "Coastal high"},
    "Zone 5": {"basic_wind_speed": 56.0, "description": "Hurricane prone"}
}

ALL_WIND_ZONES = {
    "EU": EU_WIND_ZONES, "CN": CN_WIND_ZONES, "UK": UK_WIND_ZONES,
    "MY": MY_WIND_ZONES, "US": US_WIND_ZONES
}

# ===== TERRAIN CATEGORIES =====
EU_TERRAIN = {"0": {"name": "Sea", "z0": 0.003, "z_min": 1, "alpha": 0.11},
              "I": {"name": "Open country", "z0": 0.01, "z_min": 1, "alpha": 0.12},
              "II": {"name": "Suburban", "z0": 0.05, "z_min": 2, "alpha": 0.14},
              "III": {"name": "City centre", "z0": 0.30, "z_min": 5, "alpha": 0.20},
              "IV": {"name": "Dense urban", "z0": 1.00, "z_min": 10, "alpha": 0.24}}

CN_TERRAIN = {"A": {"name": "Open sea", "z0": 0.003, "z_min": 1, "alpha": 0.12},
              "B": {"name": "Open country", "z0": 0.02, "z_min": 2, "alpha": 0.15},
              "C": {"name": "Suburban", "z0": 0.05, "z_min": 3, "alpha": 0.18},
              "D": {"name": "City centre", "z0": 0.30, "z_min": 5, "alpha": 0.22}}

UK_TERRAIN = {"1": {"name": "Open country", "z0": 0.01, "z_min": 1, "alpha": 0.12},
              "2": {"name": "Suburban", "z0": 0.05, "z_min": 2, "alpha": 0.14},
              "3": {"name": "City centre", "z0": 0.30, "z_min": 5, "alpha": 0.20},
              "4": {"name": "Dense urban", "z0": 1.00, "z_min": 10, "alpha": 0.24}}

MY_TERRAIN = {"0": {"name": "Sea", "z0": 0.003, "z_min": 1, "alpha": 0.11},
              "I": {"name": "Open country", "z0": 0.01, "z_min": 1, "alpha": 0.12},
              "II": {"name": "Suburban", "z0": 0.05, "z_min": 2, "alpha": 0.14},
              "III": {"name": "City centre", "z0": 0.30, "z_min": 5, "alpha": 0.20},
              "IV": {"name": "Dense urban", "z0": 1.00, "z_min": 10, "alpha": 0.24}}

US_TERRAIN = {"A": {"name": "Open water", "z0": 0.003, "z_min": 1, "alpha": 0.11},
              "B": {"name": "Open country", "z0": 0.02, "z_min": 1, "alpha": 0.12},
              "C": {"name": "Suburban", "z0": 0.05, "z_min": 2, "alpha": 0.14},
              "D": {"name": "City centre", "z0": 0.30, "z_min": 5, "alpha": 0.20}}

ALL_TERRAIN = {"EU": EU_TERRAIN, "CN": CN_TERRAIN, "UK": UK_TERRAIN, "MY": MY_TERRAIN, "US": US_TERRAIN}

# ===== CABLE SPECS =====
CABLE_SPECS = {
    "6x19 Galvanized (EU)": {
        "diameters": [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40],
        "breaking_load": {6: 20.0, 8: 35.0, 10: 55.0, 12: 80.0, 14: 105.0, 16: 140.0,
                          18: 180.0, 20: 220.0, 22: 260.0, 24: 310.0, 26: 360.0,
                          28: 420.0, 30: 480.0, 32: 540.0, 36: 680.0, 40: 840.0},
        "weight_kg_m": {6: 0.14, 8: 0.25, 10: 0.40, 12: 0.58, 14: 0.78, 16: 1.02,
                        18: 1.30, 20: 1.60, 22: 1.94, 24: 2.30, 26: 2.70, 28: 3.20,
                        30: 3.70, 32: 4.20, 36: 5.30, 40: 6.60},
        "min_factor": 1.5, "description": "Galvanized steel wire rope - EU"
    },
    "GB/T 20118 (China)": {
        "diameters": [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40],
        "breaking_load": {6: 22.0, 8: 38.0, 10: 60.0, 12: 85.0, 14: 110.0, 16: 150.0,
                          18: 190.0, 20: 230.0, 22: 270.0, 24: 320.0, 26: 370.0,
                          28: 430.0, 30: 490.0, 32: 550.0, 36: 690.0, 40: 850.0},
        "weight_kg_m": {6: 0.14, 8: 0.25, 10: 0.40, 12: 0.58, 14: 0.78, 16: 1.02,
                        18: 1.30, 20: 1.60, 22: 1.94, 24: 2.30, 26: 2.70, 28: 3.20,
                        30: 3.70, 32: 4.20, 36: 5.30, 40: 6.60},
        "min_factor": 1.6, "description": "GB/T 20118 - China"
    },
    "BS 302 (UK)": {
        "diameters": [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40],
        "breaking_load": {6: 21.0, 8: 36.0, 10: 56.0, 12: 82.0, 14: 108.0, 16: 142.0,
                          18: 182.0, 20: 225.0, 22: 265.0, 24: 315.0, 26: 365.0,
                          28: 425.0, 30: 485.0, 32: 545.0, 36: 685.0, 40: 845.0},
        "weight_kg_m": {6: 0.14, 8: 0.25, 10: 0.40, 12: 0.58, 14: 0.78, 16: 1.02,
                        18: 1.30, 20: 1.60, 22: 1.94, 24: 2.30, 26: 2.70, 28: 3.20,
                        30: 3.70, 32: 4.20, 36: 5.30, 40: 6.60},
        "min_factor": 1.5, "description": "BS 302 - UK"
    },
    "MS EN 1993-1-11 (Malaysia)": {
        "diameters": [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40],
        "breaking_load": {6: 20.0, 8: 35.0, 10: 55.0, 12: 80.0, 14: 105.0, 16: 140.0,
                          18: 180.0, 20: 220.0, 22: 260.0, 24: 310.0, 26: 360.0,
                          28: 420.0, 30: 480.0, 32: 540.0, 36: 680.0, 40: 840.0},
        "weight_kg_m": {6: 0.14, 8: 0.25, 10: 0.40, 12: 0.58, 14: 0.78, 16: 1.02,
                        18: 1.30, 20: 1.60, 22: 1.94, 24: 2.30, 26: 2.70, 28: 3.20,
                        30: 3.70, 32: 4.20, 36: 5.30, 40: 6.60},
        "min_factor": 1.5, "description": "MS EN 1993-1-11 - Malaysia"
    },
    "ASTM A1023 (US)": {
        "diameters": [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40],
        "breaking_load": {6: 23.0, 8: 40.0, 10: 62.0, 12: 88.0, 14: 115.0, 16: 155.0,
                          18: 195.0, 20: 240.0, 22: 280.0, 24: 330.0, 26: 380.0,
                          28: 440.0, 30: 500.0, 32: 560.0, 36: 700.0, 40: 860.0},
        "weight_kg_m": {6: 0.14, 8: 0.25, 10: 0.40, 12: 0.58, 14: 0.78, 16: 1.02,
                        18: 1.30, 20: 1.60, 22: 1.94, 24: 2.30, 26: 2.70, 28: 3.20,
                        30: 3.70, 32: 4.20, 36: 5.30, 40: 6.60},
        "min_factor": 1.5, "description": "ASTM A1023 - US"
    }
}

# ===== SECTION PROPERTIES =====
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
    "I-300": {"A": 6720, "I": 136e6, "W_el": 907e3, "i": 142.3, "weight": 52.8},
    "I-350": {"A": 9020, "I": 226e6, "W_el": 1290e3, "i": 158.3, "weight": 70.8},
    "I-400": {"A": 11800, "I": 348e6, "W_el": 1740e3, "i": 171.8, "weight": 92.6}
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
if "selected_standard" not in st.session_state:
    st.session_state.selected_standard = "EU"

# Materials State
if "materials" not in st.session_state:
    st.session_state.materials = {
        "standard": "EU",
        "steel_grade": "S355 (EN 10025)",
        "section_size": "CHS 168.3x7.1",
        "fabric_type": "PVC-coated Polyester",
        "fabric_thickness": 0.8,
        "wire_rope_type": "6x19 Galvanized (EU)",
        "wire_rope_diameter": 12,
        "num_bays": 2,
        "tie_down_angle": 45,
        "wind_zone": "Zone 2",
        "terrain_category": "II",
        "building_height": 10.0,
        "importance_factor": 1.0,
        "safety_factor": 1.5
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

def get_steel_grades_for_standard(standard):
    if standard == "EU": return EU_STEEL_GRADES
    elif standard == "CN": return CN_STEEL_GRADES
    elif standard == "UK": return UK_STEEL_GRADES
    elif standard == "MY": return MY_STEEL_GRADES
    elif standard == "US": return US_STEEL_GRADES
    else: return EU_STEEL_GRADES

def get_wind_zones_for_standard(standard):
    return ALL_WIND_ZONES.get(standard, ALL_WIND_ZONES["EU"])

def get_terrain_categories_for_standard(standard):
    return ALL_TERRAIN.get(standard, ALL_TERRAIN["EU"])

def calculate_wind_pressure_standard(wind_zone, terrain_category, height, importance_factor, standard="EU"):
    wind_zones = get_wind_zones_for_standard(standard)
    terrain_cats = get_terrain_categories_for_standard(standard)
    
    wind_data = wind_zones.get(wind_zone, list(wind_zones.values())[0])
    terrain = terrain_cats.get(terrain_category, list(terrain_cats.values())[0])
    
    vb = wind_data["basic_wind_speed"]
    z0 = terrain["z0"]
    z_min = terrain["z_min"]
    alpha = terrain["alpha"]
    
    z = max(height, z_min)
    if z <= z_min:
        ce = 1.0
    else:
        ce = 0.86 * (z / 10)**(2 * alpha)
    
    qp = 0.5 * 1.225 * (vb * ce)**2 / 1000
    wind_pressure = qp * importance_factor
    
    return {
        "basic_wind_speed": vb,
        "terrain_roughness": terrain["name"],
        "height_factor": ce,
        "peak_pressure": qp,
        "design_pressure": wind_pressure,
        "zone_description": wind_data["description"],
        "standard": standard,
        "standard_label": get_standard_label(standard)
    }

def calculate_steel_capacity_standard(grade, section, length, safety_factor, standard="EU"):
    steel_grades = get_steel_grades_for_standard(standard)
    
    # FIX: If grade not found, use first available grade
    if grade not in steel_grades:
        grade = list(steel_grades.keys())[0] if steel_grades else "S355 (EN 10025)"
    
    steel = steel_grades[grade]
    section_data = SECTION_PROPERTIES.get(section, SECTION_PROPERTIES["CHS 168.3x7.1"])
    
    fy = steel["fy"]
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
    cable_data = CABLE_SPECS.get(cable_type, CABLE_SPECS["6x19 Galvanized (EU)"])
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
        selected_diameter = cable_data["diameters"][-1] if cable_data["diameters"] else 12
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
# STRUCTURAL HEALTH REPORT FUNCTION
# ============================================================
def generate_structural_health_report(params, materials):
    """Generate comprehensive structural health report using selected standard"""
    span = params.get("B", 10.0)
    laa = params.get("LAA", 15.0)
    rise = params.get("A", 6.0)
    
    m = materials
    standard = m.get("standard", "EU")
    
    # Wind analysis
    wind_result = calculate_wind_pressure_standard(
        m.get("wind_zone", "Zone 2"),
        m.get("terrain_category", "II"),
        m.get("building_height", 10.0),
        m.get("importance_factor", 1.0),
        standard
    )
    
    # Steel capacity - FIXED with safe grade handling
    steel_grade = m.get("steel_grade", "S355 (EN 10025)")
    steel_capacity = calculate_steel_capacity_standard(
        steel_grade,
        m.get("section_size", "CHS 168.3x7.1"),
        span,
        m.get("safety_factor", 1.5),
        standard
    )
    
    membrane_area = span * laa * 1.1
wind_force = wind_result["design_pressure"] * membrane_area
    
    num_anchors = m.get("num_bays", 2) * 2
    tie_down_force = (wind_force * 0.8) / num_anchors if num_anchors > 0 else 0
    
    cable_selection = calculate_cable_size_standard(
        tie_down_force,
        m.get("safety_factor", 1.5),
        m.get("wire_rope_type", "6x19 Galvanized (EU)")
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
    elif cable_selection["capacity_ratio"] > 0.9:
        health_score -= 5
    
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

def render_structural_health_report(report):
    """Render the structural health report with all details"""
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
        st.write(f"**Terrain Category:** {wind['terrain_roughness']}")
    with col2:
        st.write(f"**Height Factor:** {wind['height_factor']:.2f}")
        st.write(f"**Peak Pressure:** {wind['peak_pressure']:.2f} kN/m²")
        st.write(f"**Design Pressure:** {wind['design_pressure']:.2f} kN/m²")
    
    st.markdown("---")
    
    st.subheader("🏗️ Steel Member Capacity")
    steel = report["steel_capacity"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Standard:** {steel['standard_label']}")
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
    st.title("🏗️ SDS Design Studio - International Standards")
    st.caption("Design with EU, China, British, Malaysian, and US Standards")
    
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
        standard = st.session_state.selected_standard
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="icon">📊</div>
            <div class="value">{get_standard_label(standard)}</div>
            <div class="label">Current Standard</div>
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
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{proj.get('name', 'Untitled')}** — {proj.get('client', 'Unknown')}")
                st.caption(f"📌 {proj.get('typology', 'Unknown')} | {get_standard_label(proj.get('standard', 'EU'))}")
            with col2:
                if st.button("Open", key=f"dash_load_{proj.get('file')}"):
                    if load_project_from_file(proj.get('file')):
                        st.rerun()
            with col3:
                st.caption(proj.get("date", "")[:10])
            st.divider()

def render_workspace():
    params = st.session_state.params
    materials = st.session_state.materials
    typ_key = st.session_state.typology
    typ = TYPOLOGIES[typ_key]
    info = st.session_state.project_info
    standard = materials.get("standard", "EU")
    
    st.markdown("## 🧠 Design Workspace")
    st.caption(f"🇪🇺🇨🇳🇬🇧🇲🇾🇺🇸 {get_standard_label(standard)} Compliant")
    
    # Health Report Button - VISIBLE at top
    col_report1, col_report2 = st.columns([4, 1])
    with col_report2:
        if st.button("📊 Generate Health Report", use_container_width=True, type="primary"):
            st.session_state.show_structural_report = True
            st.rerun()
    
    # Show Health Report if requested
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
        
        # Standard Selection
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
        
        # Steel Materials
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🏗️ Steel Materials</div>', unsafe_allow_html=True)
        
        steel_grades = get_steel_grades_for_standard(standard)
        steel_grades_list = list(steel_grades.keys())
        current_grade = materials.get("steel_grade", steel_grades_list[0] if steel_grades_list else "S355 (EN 10025)")
        if current_grade not in steel_grades_list:
            current_grade = steel_grades_list[0] if steel_grades_list else "S355 (EN 10025)"
        
        materials["steel_grade"] = st.selectbox(
            "Steel Grade",
            steel_grades_list,
            index=steel_grades_list.index(current_grade),
            key="steel_grade_select"
        )
        
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
        
        materials["fabric_type"] = st.selectbox(
            "Fabric Type",
            ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"],
            index=0,
            key="fabric_select"
        )
        materials["fabric_thickness"] = st.selectbox(
            "Thickness (mm)",
            [0.5, 0.8, 1.0, 1.2],
            index=1,
            key="thickness_select"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Wind Analysis
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🌪️ Wind Analysis</div>', unsafe_allow_html=True)
        
        wind_zones = get_wind_zones_for_standard(standard)
        wind_zone_list = list(wind_zones.keys())
        current_wind = materials.get("wind_zone", wind_zone_list[0] if wind_zone_list else "Zone 2")
        if current_wind not in wind_zone_list:
            current_wind = wind_zone_list[0] if wind_zone_list else "Zone 2"
        
        materials["wind_zone"] = st.selectbox(
            "Wind Zone",
            wind_zone_list,
            index=wind_zone_list.index(current_wind),
            key="wind_select"
        )
        
        terrain_cats = get_terrain_categories_for_standard(standard)
        terrain_list = list(terrain_cats.keys())
        current_terrain = materials.get("terrain_category", terrain_list[0] if terrain_list else "II")
        if current_terrain not in terrain_list:
            current_terrain = terrain_list[0] if terrain_list else "II"
        
        materials["terrain_category"] = st.selectbox(
            "Terrain Category",
            terrain_list,
            index=terrain_list.index(current_terrain),
            key="terrain_select"
        )
        
        materials["building_height"] = st.number_input(
            "Building Height (m)",
            min_value=2.0, max_value=50.0, step=0.5,
            value=float(materials.get("building_height", 10.0)),
            key="building_height"
        )
        materials["importance_factor"] = st.slider(
            "Importance Factor",
            min_value=0.8, max_value=1.5, step=0.1,
            value=float(materials.get("importance_factor", 1.0)),
            key="importance_factor"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Bracing & Tie-Downs
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔗 Bracing & Tie-Downs</div>', unsafe_allow_html=True)
        materials["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], index=1, key="num_bays")
        materials["tie_down_angle"] = st.slider("Tie-Down Angle (°)", 20, 70, 45, 5, key="tie_down_angle")
        
        cable_options = list(CABLE_SPECS.keys())
        current_cable = materials.get("wire_rope_type", cable_options[0] if cable_options else "6x19 Galvanized (EU)")
        if current_cable not in cable_options:
            current_cable = cable_options[0] if cable_options else "6x19 Galvanized (EU)"
        
        materials["wire_rope_type"] = st.selectbox(
            "Cable Type",
            cable_options,
            index=cable_options.index(current_cable),
            key="cable_type"
        )
        
        available_diameters = CABLE_SPECS[materials["wire_rope_type"]]["diameters"]
        current_diameter = materials.get("wire_rope_diameter", available_diameters[0] if available_diameters else 12)
        if current_diameter not in available_diameters:
            current_diameter = available_diameters[0] if available_diameters else 12
        
        materials["wire_rope_diameter"] = st.selectbox(
            "Cable Diameter (mm)",
            available_diameters,
            index=available_diameters.index(current_diameter) if current_diameter in available_diameters else 0,
            key="cable_diameter"
        )
        
        materials["safety_factor"] = st.number_input(
            "Safety Factor",
            min_value=1.0, max_value=3.0, step=0.1,
            value=float(materials.get("safety_factor", 1.5)),
            key="safety_factor"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Comments
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">💬 Notes</div>', unsafe_allow_html=True)
        comments = st.text_area("", value=st.session_state.comments, height=80, placeholder="Add design notes...", key="comments_area")
        st.session_state.comments = comments
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.subheader("🔬 3D Model")
        
        if typ_key == "custom":
            fig = generate_custom(params)
        else:
            fig = GENERATORS[typ_key](params, materials if typ_key == "saddle_span" else None)
        
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
            if st.button("📊 Health Report", use_container_width=True, key="report_btn"):
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
    
    # Q&A
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">❓ Design Confirmation</div>', unsafe_allow_html=True)
    for i, q in enumerate(typ["qa"]):
        key = f"qa_{i}"
        default = st.session_state.qa_answers.get(key, "Yes")
        ans = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes", "No", "Not Sure"].index(default), key=f"qa_{i}")
        st.session_state.qa_answers[key] = ans
    st.markdown('</div>', unsafe_allow_html=True)
    
    save_cache()

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
        name = st.text_input("Project Name *", placeholder="e.g., KLCC Canopy")
        client = st.text_input("Client Name *", placeholder="e.g., KLCC Holdings")
        location = st.text_input("Location", placeholder="e.g., Kuala Lumpur")
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
    st.caption(f"🌍 {get_standard_label(st.session_state.selected_standard)} Compliant")
    
    cols = st.columns(2)
    idx = 0
    for key, typ in TYPOLOGIES.items():
        with cols[idx % 2]:
            if st.button(f"{typ['icon']} {typ['name']}", use_container_width=True, key=f"typology_{key}"):
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
st.caption("SDS Design Studio | EU / China / British / Malaysia / USA Standards | v7.1")

save_cache()
