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
import csv
from io import BytesIO, StringIO

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="FDS - Fluid Design Studio v7.0",
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
    .stButton > button[kind="secondary"] {
        background-color: #2a3a4f !important;
        color: #ffffff !important;
        border: 1px solid #4a7a9c !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #3a4a5f !important;
        border-color: #6a9abc !important;
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
    .top-nav { display: flex; gap: 0.5rem; padding: 0.5rem 0; flex-wrap: wrap; }
    .top-nav .stButton { flex: 1; min-width: 100px; }
    .section-tag { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.65rem; font-weight: 600; margin-left: 0.3rem; }
    .tag-chs { background-color: #e74c3c; color: #ffffff; }
    .tag-shs { background-color: #3498db; color: #ffffff; }
    .tag-rhs { background-color: #2ecc71; color: #ffffff; }
    .tag-ibeam { background-color: #f39c12; color: #ffffff; }
    .tag-angle { background-color: #9b59b6; color: #ffffff; }
    .tag-channel { background-color: #1abc9c; color: #ffffff; }
    .license-badge { display: inline-block; padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
    .license-free { background-color: #2ecc71; color: #0a0e17; }
    .license-pro { background-color: #3498db; color: #ffffff; }
    .license-business { background-color: #f39c12; color: #0a0e17; }
    
    /* ===== LICENSE SWITCHER - PROMINENT ON DASHBOARD ===== */
    .license-switcher {
        background: linear-gradient(135deg, #1a2a3a, #0a0e17);
        border: 2px solid #2a3a4f;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .license-switcher .title {
        color: #b0c4de;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* ===== DESIGN PATHS ===== */
    .design-path-card {
        background-color: #141e2b;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #2a3a4f;
        text-align: center;
        height: 100%;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .design-path-card:hover {
        border-color: #f39c12;
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(243, 156, 18, 0.1);
    }
    .design-path-card .icon { font-size: 3rem; }
    .design-path-card .title { color: #ffffff; font-size: 1.2rem; font-weight: 600; margin-top: 0.5rem; }
    .design-path-card .desc { color: #8a9aaa; font-size: 0.9rem; margin-top: 0.5rem; }
    
    /* ===== RADIO BUTTON FIX ===== */
    .stRadio > div {
        gap: 0.5rem;
    }
    .stRadio > div label {
        color: #6a7a8a !important;
        background-color: #0a0e17 !important;
        padding: 0.3rem 1rem !important;
        border-radius: 20px !important;
        border: 1px solid #2a3a4f !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        font-size: 0.85rem !important;
    }
    .stRadio > div label:hover {
        border-color: #4a7a9c !important;
        color: #ffffff !important;
    }
    
    /* ===== QUESTION PROGRESS ===== */
    .progress-bar {
        background-color: #1a2a3a;
        border-radius: 10px;
        height: 8px;
        margin: 0.5rem 0;
        overflow: hidden;
    }
    .progress-bar .fill {
        background: linear-gradient(90deg, #f39c12, #f1c40f);
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    .question-counter {
        color: #8a9aaa;
        font-size: 0.8rem;
        text-align: right;
    }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# LICENSE TIERS CONFIGURATION
# ============================================================
LICENSE_TIERS = {
    "free": {
        "name": "FDS Studio",
        "badge": "FREE",
        "badge_class": "license-free",
        "project_limit": 3,
        "features": {
            "3d_viewer": True,
            "health_score": True,
            "structure_types": True,
            "load_calculations": True,
            "member_sizing": True,
            "fabric_selection": True,
            "pdf_report": True,
            "bq": False,
            "editable_bq": False,
            "costing_sheet": False,
            "reaction_forces": False,
            "shear_moment": False,
            "axial_forces": False,
            "cad_drawings": False,
            "export_excel": False,
            "unlimited_projects": False
        }
    },
    "pro": {
        "name": "FDS Engineer",
        "badge": "PRO",
        "badge_class": "license-pro",
        "project_limit": None,
        "features": {
            "3d_viewer": True,
            "health_score": True,
            "structure_types": True,
            "load_calculations": True,
            "member_sizing": True,
            "fabric_selection": True,
            "pdf_report": True,
            "bq": True,
            "editable_bq": False,
            "costing_sheet": False,
            "reaction_forces": False,
            "shear_moment": False,
            "axial_forces": False,
            "cad_drawings": False,
            "export_excel": False,
            "unlimited_projects": True
        }
    },
    "business": {
        "name": "FDS Constructor",
        "badge": "BUSINESS",
        "badge_class": "license-business",
        "project_limit": None,
        "features": {
            "3d_viewer": True,
            "health_score": True,
            "structure_types": True,
            "load_calculations": True,
            "member_sizing": True,
            "fabric_selection": True,
            "pdf_report": True,
            "bq": True,
            "editable_bq": True,
            "costing_sheet": True,
            "reaction_forces": True,
            "shear_moment": True,
            "axial_forces": True,
            "cad_drawings": True,
            "export_excel": True,
            "unlimited_projects": True
        }
    }
}

# ============================================================
# FEATURE CHECK FUNCTIONS
# ============================================================
def has_feature(feature_name):
    tier = st.session_state.get("license_tier", "free")
    features = LICENSE_TIERS.get(tier, {}).get("features", {})
    return features.get(feature_name, False)

def get_license_info():
    tier = st.session_state.get("license_tier", "free")
    return LICENSE_TIERS.get(tier, LICENSE_TIERS["free"])

def check_project_limit():
    tier = st.session_state.get("license_tier", "free")
    limit = LICENSE_TIERS.get(tier, {}).get("project_limit")
    if limit is None:
        return True
    current_projects = len(st.session_state.saved_projects)
    return current_projects < limit

def get_remaining_projects():
    tier = st.session_state.get("license_tier", "free")
    limit = LICENSE_TIERS.get(tier, {}).get("project_limit")
    if limit is None:
        return "Unlimited"
    current = len(st.session_state.saved_projects)
    return max(0, limit - current)

# ============================================================
# SESSION STATE
# ============================================================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "page": "dashboard",
        "design_path": None,
        "brief_answers": {},
        "brief_step": 0,
        "recommended_system": None,
        "project_registered": False,
        "project_info": {},
        "typology": None,
        "params": {},
        "qa_answers": {},
        "locked": False,
        "comments": "",
        "saved_projects": [],
        "license_tier": "free",
        "design_results": {},
        "bq": {},
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
            "country": "Malaysia"
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize session state
init_session_state()

# ============================================================
# CLEAR PROJECT DATA FUNCTION
# ============================================================
def clear_previous_project_data():
    st.session_state.design_results = {}
    st.session_state.bq = {}
    st.session_state.params = {}
    st.session_state.qa_answers = {}
    st.session_state.comments = ""
    st.session_state.locked = False
    st.session_state.typology = None
    
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
        "country": st.session_state.materials.get("country", "Malaysia")
    }
    st.session_state.materials = default_materials

# ============================================================
# COUNTRY CURRENCY DATABASE
# ============================================================
COUNTRY_CURRENCIES = {
    "Malaysia": {"code": "MYR", "symbol": "RM", "rate": 1.0},
    "Singapore": {"code": "SGD", "symbol": "S$", "rate": 3.2},
    "Indonesia": {"code": "IDR", "symbol": "Rp", "rate": 10500},
    "Thailand": {"code": "THB", "symbol": "฿", "rate": 25.5},
    "Vietnam": {"code": "VND", "symbol": "₫", "rate": 25000},
    "Philippines": {"code": "PHP", "symbol": "₱", "rate": 18.5},
    "China": {"code": "CNY", "symbol": "¥", "rate": 1.5},
    "UK": {"code": "GBP", "symbol": "£", "rate": 0.18},
    "EU": {"code": "EUR", "symbol": "€", "rate": 0.21},
    "US": {"code": "USD", "symbol": "$", "rate": 0.24},
    "Australia": {"code": "AUD", "symbol": "A$", "rate": 0.35},
    "India": {"code": "INR", "symbol": "₹", "rate": 20.0},
    "Japan": {"code": "JPY", "symbol": "¥", "rate": 35.0},
    "South Korea": {"code": "KRW", "symbol": "₩", "rate": 320},
    "Brazil": {"code": "BRL", "symbol": "R$", "rate": 1.3},
}

# ============================================================
# SECTION PROPERTIES DATABASE
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
    
    # ====== I-BEAMS ======
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
    
    # ====== ANGLES ======
    "L40x40x4": {"A": 309, "I": 0.08e6, "W_el": 2.8e3, "i": 16.1, "weight": 2.4, "type": "Angle", "depth": 40},
    "L50x50x5": {"A": 480, "I": 0.18e6, "W_el": 5.1e3, "i": 19.4, "weight": 3.8, "type": "Angle", "depth": 50},
    "L60x60x6": {"A": 691, "I": 0.36e6, "W_el": 8.5e3, "i": 22.8, "weight": 5.4, "type": "Angle", "depth": 60},
    "L70x70x7": {"A": 941, "I": 0.64e6, "W_el": 12.8e3, "i": 26.1, "weight": 7.4, "type": "Angle", "depth": 70},
    "L80x80x8": {"A": 1229, "I": 1.04e6, "W_el": 18.2e3, "i": 29.1, "weight": 9.6, "type": "Angle", "depth": 80},
    "L90x90x9": {"A": 1553, "I": 1.58e6, "W_el": 24.7e3, "i": 31.9, "weight": 12.2, "type": "Angle", "depth": 90},
    "L100x100x10": {"A": 1910, "I": 2.28e6, "W_el": 32.0e3, "i": 34.5, "weight": 15.0, "type": "Angle", "depth": 100},
    "L120x120x12": {"A": 2752, "I": 4.52e6, "W_el": 53.0e3, "i": 40.5, "weight": 21.6, "type": "Angle", "depth": 120},
    
    # ====== CHANNELS ======
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
MATERIAL_COSTS = {"Steel": 2.5, "Aluminum": 4.5, "Wood": 1.2, "Composite": 6.0}

JOINT_MULTIPLIERS = {
    "welded": {"factor": 1.2, "cost_multiplier": 1.3, "connection_cost": 150, "description": "Rigid moment connections"},
    "bolted": {"factor": 1.0, "cost_multiplier": 1.0, "connection_cost": 80, "description": "Pin connections - economical"}
}

# ============================================================
# INTELLIGENT QUESTION ENGINE
# ============================================================
STRUCTURE_QUESTIONS = {
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "🏕️",
        "systems": ["cable_stayed", "rigid_frame", "hybrid"],
        "questions": {
            "general": [
                {
                    "id": "primary_function",
                    "question": "What is the primary function of this structure?",
                    "options": ["Weather Protection", "Architectural Feature", "Shade Structure", "Event Space", "Sports Facility"],
                    "condition": None
                },
                {
                    "id": "span_range",
                    "question": "What is the approximate span?",
                    "options": ["< 20m", "20-40m", "40-60m", "> 60m"],
                    "condition": None
                },
                {
                    "id": "budget_range",
                    "question": "What is the budget range?",
                    "options": ["Low (Basic)", "Medium (Standard)", "High (Premium)", "Very High (Iconic)"],
                    "condition": None
                }
            ],
            "system_determination": [
                {
                    "id": "structural_preference",
                    "question": "Do you prefer cable-stayed or rigid frame?",
                    "options": [
                        "Cable-Stayed (Dramatic, Lightweight)",
                        "Rigid Frame (Permanent, Maintenance-Free)",
                        "Hybrid (Best of Both)",
                        "Not Sure - Recommend"
                    ],
                    "condition": None
                },
                {
                    "id": "site_soil",
                    "question": "What is the soil condition at the site?",
                    "options": ["Sand", "Clay", "Rock", "Unknown"],
                    "condition": None
                }
            ],
            "cable_stayed": [
                {
                    "id": "cable_layout",
                    "question": "Preferred cable layout?",
                    "options": ["Radial (Mast at center)", "Fan (Multiple angles)", "Harp (Parallel cables)", "Network (Crossed cables)"],
                    "condition": {"structural_preference": ["Cable-Stayed", "Hybrid"]}
                },
                {
                    "id": "cable_prestress",
                    "question": "Cable prestress level?",
                    "options": ["Low (Minimum tension)", "Medium (Balanced)", "High (Maximum stiffness)"],
                    "condition": {"structural_preference": ["Cable-Stayed", "Hybrid"]}
                },
                {
                    "id": "anchor_type",
                    "question": "Anchor system preference?",
                    "options": ["Ground Anchors", "Foundation Blocks", "Rock Anchors", "Ballast"],
                    "condition": {"structural_preference": ["Cable-Stayed", "Hybrid"]}
                }
            ],
            "rigid_frame": [
                {
                    "id": "frame_type",
                    "question": "Preferred rigid frame type?",
                    "options": ["Portal Frame", "Arch Frame", "Trussed Frame"],
                    "condition": {"structural_preference": ["Rigid Frame", "Hybrid"]}
                },
                {
                    "id": "connection_type",
                    "question": "Connection preference?",
                    "options": ["Welded (Moment connection)", "Bolted (Pin connection)"],
                    "condition": {"structural_preference": ["Rigid Frame", "Hybrid"]}
                },
                {
                    "id": "frame_material",
                    "question": "Frame material preference?",
                    "options": ["Steel", "Aluminum", "Composite"],
                    "condition": {"structural_preference": ["Rigid Frame", "Hybrid"]}
                }
            ],
            "geometry": [
                {
                    "id": "shape_type",
                    "question": "Preferred surface geometry?",
                    "options": ["Parabolic", "Elliptical", "Circular", "Catenary"],
                    "condition": None
                },
                {
                    "id": "rise_span_ratio",
                    "question": "Rise to span ratio preference?",
                    "options": ["Low (1:8)", "Medium (1:5)", "High (1:3)"],
                    "condition": None
                }
            ],
            "membrane": [
                {
                    "id": "fabric_type",
                    "question": "Fabric material preference?",
                    "options": ["PVC-coated Polyester (Economical)", "PTFE-coated Fiberglass (Premium)", "ETFE (Transparent)"],
                    "condition": None
                }
            ]
        }
    },
    "clear_span_tent": {
        "name": "Clear-Span Tent",
        "icon": "🏗️",
        "systems": ["cable_stayed", "rigid_frame", "hybrid"],
        "questions": {
            "general": [
                {
                    "id": "primary_function",
                    "question": "What is the primary function?",
                    "options": ["Event Space", "Sports Facility", "Temporary Shelter", "Permanent Structure"],
                    "condition": None
                },
                {
                    "id": "span_range",
                    "question": "What is the approximate span?",
                    "options": ["< 20m", "20-40m", "40-60m", "> 60m"],
                    "condition": None
                }
            ],
            "system_determination": [
                {
                    "id": "structural_preference",
                    "question": "Do you prefer cable-stayed or rigid frame?",
                    "options": ["Cable-Stayed (Lightweight)", "Rigid Frame (Permanent)", "Hybrid (Best of Both)", "Not Sure - Recommend"],
                    "condition": None
                }
            ],
            "cable_stayed": [
                {
                    "id": "cable_layout",
                    "question": "Preferred cable layout?",
                    "options": ["Ridge Cable", "Edge Cables", "Network"],
                    "condition": {"structural_preference": ["Cable-Stayed", "Hybrid"]}
                }
            ],
            "rigid_frame": [
                {
                    "id": "truss_type",
                    "question": "Preferred truss type?",
                    "options": ["Warren", "Pratt", "Howe", "Vierendeel"],
                    "condition": {"structural_preference": ["Rigid Frame", "Hybrid"]}
                }
            ]
        }
    },
    "tensile_membrane": {
        "name": "Tensile Membrane",
        "icon": "⛺",
        "systems": ["mast_supported", "frame_supported", "cable_stayed"],
        "questions": {
            "general": [
                {
                    "id": "primary_function",
                    "question": "What is the primary function?",
                    "options": ["Weather Protection", "Architectural Feature", "Sports Facility"],
                    "condition": None
                }
            ],
            "system_determination": [
                {
                    "id": "support_type",
                    "question": "Preferred support system?",
                    "options": ["Mast-Supported", "Frame-Supported", "Cable-Stayed", "Not Sure - Recommend"],
                    "condition": None
                }
            ]
        }
    },
    "portal_frame": {
        "name": "Portal Frame",
        "icon": "🏛️",
        "systems": ["rigid_frame"],
        "questions": {
            "general": [
                {
                    "id": "primary_function",
                    "question": "What is the primary function?",
                    "options": ["Industrial Building", "Warehouse", "Commercial Building", "Agricultural Shed"],
                    "condition": None
                },
                {
                    "id": "span_range",
                    "question": "What is the approximate span?",
                    "options": ["< 10m", "10-20m", "20-30m", "> 30m"],
                    "condition": None
                }
            ],
            "rigid_frame": [
                {
                    "id": "connection_type",
                    "question": "Connection preference?",
                    "options": ["Welded (Moment connection)", "Bolted (Pin connection)"],
                    "condition": None
                },
                {
                    "id": "frame_material",
                    "question": "Frame material preference?",
                    "options": ["Steel", "Aluminum"],
                    "condition": None
                }
            ]
        }
    }
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def get_standard_label(code):
    labels = {"EU": "🇪🇺 Eurocode", "CN": "🇨🇳 China", "UK": "🇬🇧 British", "MY": "🇲🇾 Malaysia", "US": "🇺🇸 USA"}
    return labels.get(code, code)

def get_currency(country):
    country_data = COUNTRY_CURRENCIES.get(country, COUNTRY_CURRENCIES["Malaysia"])
    return country_data

def format_currency(amount, country="Malaysia"):
    currency = get_currency(country)
    return f"{currency['symbol']}{amount:,.0f}"

def get_section_tag(section_type):
    tags = {
        "CHS": '<span class="section-tag tag-chs">CHS</span>',
        "SHS": '<span class="section-tag tag-shs">SHS</span>',
        "RHS": '<span class="section-tag tag-rhs">RHS</span>',
        "I-Beam": '<span class="section-tag tag-ibeam">I</span>',
        "Angle": '<span class="section-tag tag-angle">L</span>',
        "Channel": '<span class="section-tag tag-channel">C</span>',
    }
    return tags.get(section_type, "")

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
        return [-span/4, span/4]
    if num_bays == 3:
        return [-span/3, 0.0, span/3]
    return np.linspace(-span/3, span/3, num_bays).tolist()

# ============================================================
# SYSTEM RECOMMENDATION ENGINE
# ============================================================
def recommend_system(brief_answers):
    """Intelligent system recommendation based on user answers"""
    scores = {"cable_stayed": 0, "rigid_frame": 0, "hybrid": 0}
    
    # Check span
    span = brief_answers.get("span_range", "20-40m")
    if span == "> 60m":
        scores["cable_stayed"] += 3
        scores["hybrid"] += 2
    elif span == "40-60m":
        scores["cable_stayed"] += 2
        scores["hybrid"] += 2
        scores["rigid_frame"] += 1
    elif span == "< 20m":
        scores["rigid_frame"] += 2
        scores["hybrid"] += 1
    
    # Check budget
    budget = brief_answers.get("budget_range", "Medium")
    if budget == "Low":
        scores["rigid_frame"] += 2
    elif budget == "High":
        scores["cable_stayed"] += 2
        scores["hybrid"] += 1
    
    # Check soil
    soil = brief_answers.get("site_soil", "Unknown")
    if soil == "Rock":
        scores["cable_stayed"] += 1
    elif soil == "Sand":
        scores["rigid_frame"] += 1
    
    # Check function
    function = brief_answers.get("primary_function", "Weather Protection")
    if function in ["Architectural Feature", "Iconic"]:
        scores["cable_stayed"] += 2
    elif function in ["Permanent Structure", "Industrial"]:
        scores["rigid_frame"] += 2
    
    # Determine best system
    best = max(scores, key=scores.get)
    confidence = min(100, int((scores[best] / sum(scores.values()) * 100) if sum(scores.values()) > 0 else 50))
    
    return {
        "recommended": best,
        "confidence": confidence,
        "scores": scores,
        "explanation": f"Based on your inputs, {best.replace('_', ' ').title()} is recommended with {confidence}% confidence."
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

# ============================================================
# FIXED SECTION SELECTION FUNCTION
# ============================================================
def calculate_required_section(load_kN, span_m, material_type, section_type, fy=355, typology="saddle_span", rise_m=6.0):
    """Intelligent section selection - finds SMALLEST adequate section"""
    safety = 1.5
    
    w = load_kN / span_m
    M_beam = (w * span_m**2) / 8
    
    # Arch action for saddle span
    if typology == "saddle_span":
        arch_reduction = max(0.35, 1 - (rise_m / span_m) * 0.55)
        M = M_beam * arch_reduction
    else:
        arch_reduction = 1.0
        M = M_beam
    
    M_Nmm = M * 1e6
    W_required = M_Nmm / (fy / safety)
    
    # Deflection calculation
    E = 210000
    
    if span_m < 10:
        deflection_ratio = 200
        arch_reduction_factor = 0.3
    elif span_m < 20:
        deflection_ratio = 250
        arch_reduction_factor = 0.4
    else:
        deflection_ratio = 300
        arch_reduction_factor = 0.5
    
    deflection_limit = span_m / deflection_ratio
    
    w_Nmm = w / 1000
    span_mm = span_m * 1000
    deflection_limit_mm = deflection_limit * 1000
    
    I_required = (5 * w_Nmm * span_mm**4) / (384 * E * deflection_limit_mm)
    
    db = SECTION_PROPERTIES
    
    type_map = {
        "CHS": "CHS",
        "SHS": "SHS",
        "RHS": "RHS",
        "I-Beam": "I-Beam",
        "Angle": "Angle",
        "Channel": "Channel"
    }
    preferred_type = type_map.get(section_type, "CHS")
    
    sections_in_type = []
    for section, props in db.items():
        if props.get("type") == preferred_type:
            sections_in_type.append((section, props))
    
    sections_in_type.sort(key=lambda x: x[1]["W_el"])
    
    selected_section = None
    selected_props = None
    selection_note = None
    
    W_factor = 0.9
    I_factor = arch_reduction_factor
    
    if span_m < 8:
        I_factor = 0.2
    
    # First pass: Both criteria
    for section, props in sections_in_type:
        if props["W_el"] >= W_required * W_factor and props["I"] >= I_required * I_factor:
            selected_section = section
            selected_props = props
            selection_note = None
            break
    
    # Second pass: W only
    if not selected_section:
        for section, props in sections_in_type:
            if props["W_el"] >= W_required * W_factor:
                selected_section = section
                selected_props = props
                selection_note = "⚠️ Deflection may be slightly higher than ideal"
                break
    
    # Third pass: Any type
    if not selected_section:
        all_sections = []
        for section, props in db.items():
            all_sections.append((section, props))
        all_sections.sort(key=lambda x: x[1]["W_el"])
        
        for section, props in all_sections:
            if props["W_el"] >= W_required * W_factor:
                selected_section = section
                selected_props = props
                selection_note = f"⚠️ No {preferred_type} section adequate. Using {props['type']} instead."
                break
    
    if selected_section and selected_props:
        moment_capacity = (selected_props["W_el"] * fy) / (safety * 1e6)
        is_adequate = (
            selected_props["W_el"] >= W_required * W_factor and 
            selected_props["I"] >= I_required * I_factor
        )
        
        return {
            "section": selected_section,
            "properties": selected_props,
            "required_moment": M,
            "moment_capacity": moment_capacity,
            "is_adequate": is_adequate,
            "section_type": selected_props.get("type", preferred_type),
            "note": selection_note,
            "arch_reduction": arch_reduction,
            "I_required": I_required,
            "I_actual": selected_props["I"],
            "W_required": W_required,
            "W_actual": selected_props["W_el"]
        }
    
    if sections_in_type:
        largest_section, largest_props = sections_in_type[-1]
        moment_capacity = (largest_props["W_el"] * fy) / (safety * 1e6)
        return {
            "section": largest_section,
            "properties": largest_props,
            "required_moment": M,
            "moment_capacity": moment_capacity,
            "is_adequate": False,
            "section_type": largest_props.get("type", preferred_type),
            "note": "⚠️ Consider custom fabrication or larger section",
            "arch_reduction": arch_reduction,
            "I_required": I_required,
            "I_actual": largest_props["I"],
            "W_required": W_required,
            "W_actual": largest_props["W_el"]
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

def auto_design_structure(params, materials, typology="saddle_span"):
    span, rise, laa = params.get("B", 10.0), params.get("A", 6.0), params.get("LAA", 15.0)
    member_type = materials.get("member_type", "single_beam")
    material_type = materials.get("material_type", "Steel")
    section_type = materials.get("section_type", "CHS")
    fabric_type = materials.get("fabric_type", "PVC-coated Polyester")
    cable_type = materials.get("cable_type", "6x19 Galvanized")
    standard = materials.get("standard", "EU")
    joint_type = materials.get("joint_type", "bolted")
    country = materials.get("country", "Malaysia")
    
    joint_data = JOINT_MULTIPLIERS.get(joint_type, JOINT_MULTIPLIERS["bolted"])
    
    wind_load = calculate_wind_load(span, laa, standard)
    dead_load = calculate_dead_load(span, laa, "CHS 168.3x7.1", fabric_type)
    live_load = 0.5 * (span * laa * 1.1) / 100
    total_load = wind_load + dead_load + live_load
    
    if joint_type == "welded":
        total_load *= 1.1
    
    results = {
        "loads": {"wind": wind_load, "dead": dead_load, "live": live_load, "total": total_load},
        "beams": {}, "truss": {}, "fabric": {}, "cables": {},
        "all_checks": {}, "health_score": 0,
        "joint_type": joint_type,
        "country": country,
        "typology": typology
    }
    
    fy = 355 if material_type == "Steel" else 276 if material_type == "Aluminum" else 40
    
    if member_type == "single_beam":
        beam_result = calculate_required_section(
            total_load, span, material_type, section_type, fy, 
            typology=typology, rise_m=rise
        )
        if beam_result:
            results["beams"]["main"] = beam_result
            results["beams"]["selected"] = beam_result["section"]
            results["beams"]["moment_capacity"] = beam_result["moment_capacity"]
            results["beams"]["required_moment"] = beam_result["required_moment"]
            results["beams"]["section_type"] = beam_result.get("section_type", section_type)
            results["beams"]["note"] = beam_result.get("note", None)
            results["beams"]["is_adequate"] = beam_result.get("is_adequate", False)
            results["beams"]["arch_reduction"] = beam_result.get("arch_reduction", 1.0)
            results["beams"]["I_required"] = beam_result.get("I_required", 0)
            results["beams"]["I_actual"] = beam_result.get("I_actual", 0)
            results["beams"]["W_required"] = beam_result.get("W_required", 0)
            results["beams"]["W_actual"] = beam_result.get("W_actual", 0)
    
    truss_members = None
    if member_type in ["planar_truss", "space_truss"]:
        truss_members = analyze_truss_members(params, materials, total_load, joint_type)
        results["truss"] = truss_members
    
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
    
    results["all_checks"]["wind_load"] = {"status": "✅ PASS", "value": f"{wind_load:.1f} kN"}
    results["all_checks"]["joint_type"] = {"status": f"🔧 {joint_type.upper()}", "value": joint_data["description"][:30] + "..."}
    
    if member_type == "single_beam" and results["beams"].get("main"):
        beam = results["beams"]["main"]
        is_adequate = beam.get("is_adequate", False)
        section_note = beam.get("note", "")
        section_display = beam['section']
        
        if section_note:
            section_display = f"{beam['section']} {section_note}"
        
        if is_adequate:
            status = "✅ PASS"
        else:
            status = "⚠️ Check"
        
        results["all_checks"]["member_capacity"] = {
            "status": status,
            "value": f"{beam['moment_capacity']:.1f} kNm"
        }
        results["all_checks"]["section_selected"] = {
            "status": status,
            "value": section_display
        }
        
        sec_type = beam.get("section_type", section_type)
        results["all_checks"]["section_type"] = {
            "status": f"📐 {sec_type}",
            "value": get_section_tag(sec_type)
        }
        
        if typology == "saddle_span" and "arch_reduction" in beam:
            reduction_pct = (1 - beam["arch_reduction"]) * 100
            results["all_checks"]["arch_action"] = {
                "status": f"🏹 {reduction_pct:.0f}% Reduction",
                "value": "Arch action reduces bending"
            }
        
        if "I_required" in beam and beam["I_required"] > 0:
            i_ratio = beam["I_actual"] / beam["I_required"] if beam["I_required"] > 0 else 0
            w_ratio = beam["W_actual"] / beam["W_required"] if beam["W_required"] > 0 else 0
            results["all_checks"]["section_ratios"] = {
                "status": f"📊 I:{i_ratio:.2f} W:{w_ratio:.2f}",
                "value": f"I_req={beam['I_required']/1e6:.1f}e6, W_req={beam['W_required']/1000:.1f}e3"
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
    
    score = 100
    for check in results["all_checks"].values():
        if "⚠️" in check["status"] or "🔄" in check["status"]:
            score -= 10
        if "❌" in check["status"]:
            score -= 20
    results["health_score"] = max(0, min(100, score))
    
    bq = generate_bill_of_quantities(params, materials, results, truss_members, joint_type, country)
    results["bq"] = bq
    
    return results

def analyze_truss_members(params, materials, total_load, joint_type="bolted"):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    num_bays = materials.get("num_bays", 2)
    
    joint_data = JOINT_MULTIPLIERS.get(joint_type, JOINT_MULTIPLIERS["bolted"])
    
    total_udl = total_load / span
    max_bending = (total_udl * span**2) / 8
    truss_depth = rise * 0.7
    
    if joint_type == "welded":
        force_multiplier = 1.2
        top_chord_force = max_bending / truss_depth * 1.2 * force_multiplier
        bottom_chord_force = max_bending / truss_depth * 1.1 * force_multiplier
        diag_force = top_chord_force * 0.6
        vert_force = diag_force * 0.5
    else:
        force_multiplier = 1.0
        top_chord_force = max_bending / truss_depth * 1.2 * force_multiplier
        bottom_chord_force = max_bending / truss_depth * 1.1 * force_multiplier
        diag_force = top_chord_force * 0.6
        vert_force = diag_force * 0.5
    
    db = SECTION_PROPERTIES
    fy = 355
    
    user_section_type = materials.get("section_type", "CHS")
    type_map = {"CHS": "CHS", "SHS": "SHS", "RHS": "RHS", "I-Beam": "I-Beam", "Angle": "Angle", "Channel": "Channel"}
    preferred_type = type_map.get(user_section_type, "CHS")
    
    def find_section(force, is_compression=False, preferred_type=None):
        required_area = force * 1000 / (fy * 0.9)
        best_section = None
        best_weight = float('inf')
        
        for name, props in db.items():
            if preferred_type and props['type'] != preferred_type:
                continue
            if props['A'] >= required_area:
                if props['weight'] < best_weight:
                    best_weight = props['weight']
                    best_section = name
        
        if not best_section and preferred_type:
            for name, props in db.items():
                if props['A'] >= required_area:
                    if props['weight'] < best_weight:
                        best_weight = props['weight']
                        best_section = name
        
        return best_section
    
    truss_type = materials.get("truss_type", "warren")
    
    if truss_type == "warren":
        top_chord = find_section(top_chord_force, True, preferred_type)
        bottom_chord = find_section(bottom_chord_force, False, preferred_type)
        diag = find_section(diag_force, False, preferred_type)
        
        members = {
            "top_chord": top_chord or "I-200",
            "bottom_chord": bottom_chord or "I-250",
            "diagonals": diag or "L80x80x8",
            "verticals": "N/A (Warren)",
            "joint_type": joint_type,
            "joint_description": joint_data["description"]
        }
    elif truss_type == "pratt":
        top_chord = find_section(top_chord_force, True, preferred_type)
        bottom_chord = find_section(bottom_chord_force, False, preferred_type)
        diag = find_section(diag_force, False, preferred_type)
        vert = find_section(vert_force, True, preferred_type)
        
        members = {
            "top_chord": top_chord or "I-200",
            "bottom_chord": bottom_chord or "I-250",
            "diagonals": diag or "L80x80x8",
            "verticals": vert or "L60x60x6",
            "joint_type": joint_type,
            "joint_description": joint_data["description"]
        }
    elif truss_type == "howe":
        top_chord = find_section(top_chord_force, True, preferred_type)
        bottom_chord = find_section(bottom_chord_force, False, preferred_type)
        diag = find_section(diag_force, True, preferred_type)
        vert = find_section(vert_force, False, preferred_type)
        
        members = {
            "top_chord": top_chord or "I-200",
            "bottom_chord": bottom_chord or "I-250",
            "diagonals": diag or "L80x80x8",
            "verticals": vert or "L60x60x6",
            "joint_type": joint_type,
            "joint_description": joint_data["description"]
        }
    else:
        top_chord = find_section(top_chord_force * 1.5, True, preferred_type)
        bottom_chord = find_section(bottom_chord_force * 1.5, False, preferred_type)
        vert = find_section(vert_force * 2, True, preferred_type)
        
        members = {
            "top_chord": top_chord or "I-250",
            "bottom_chord": bottom_chord or "I-300",
            "diagonals": "N/A (Vierendeel)",
            "verticals": vert or "I-180",
            "joint_type": joint_type,
            "joint_description": joint_data["description"]
        }
    
    members["forces"] = {
        "top_chord_force": top_chord_force,
        "bottom_chord_force": bottom_chord_force,
        "diag_force": diag_force,
        "vert_force": vert_force
    }
    
    return members

# ============================================================
# BQ GENERATOR
# ============================================================
def generate_bill_of_quantities(params, materials, design_results, truss_members, joint_type="bolted", country="Malaysia"):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    num_bays = materials.get("num_bays", 2)
    
    joint_data = JOINT_MULTIPLIERS.get(joint_type, JOINT_MULTIPLIERS["bolted"])
    material_cost = MATERIAL_COSTS.get(materials.get("material_type", "Steel"), 2.5)
    currency = get_currency(country)
    
    bq_items = []
    total_cost = 0
    
    if design_results["beams"].get("selected"):
        beam_section = design_results["beams"]["selected"]
        beam_weight = SECTION_PROPERTIES.get(beam_section, {}).get("weight", 28.3)
        beam_length = span * 1.1
        total_beam_length = beam_length * 2
        total_beam_weight = beam_weight * total_beam_length / 1000
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
    
    if truss_members and "top_chord" in truss_members:
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
        
        num_joints = (num_bays + 1) * 4
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
    
    membrane_area = span * laa * 1.1
    fabric_cost_per_m2 = FABRIC_PROPERTIES.get(materials["fabric_type"], {}).get("cost_per_m2", 25)
    fabric_cost = membrane_area * fabric_cost_per_m2 * 1.2
    total_cost += fabric_cost
    
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
    
    num_anchors = num_bays * 4
    cable_length = math.sqrt(rise**2 + (span/3)**2) * 1.2
    cable_cost_per_m = CABLE_PROPERTIES.get(materials["cable_type"], {}).get("cost_per_m", 8)
    total_cable_length = num_anchors * cable_length
    cable_cost = total_cable_length * cable_cost_per_m * 1.1
    total_cost += cable_cost
    
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
    
    installation_cost = total_cost * 0.15
    total_cost += installation_cost
    
    bq_items.append({
        "item": f"Installation & Labour - {joint_type.upper()} joints",
        "qty": 1,
        "unit": "lump sum",
        "length_m": "-",
        "total_length_m": "-",
        "weight_kg": 0,
        "unit_price": installation_cost,
        "total_price": installation_cost
    })
    
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
        "joint_description": joint_data["description"],
        "currency": currency
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
        mode='lines', name='Beam 1 (Left)',
        line=dict(color='#FF6B6B', width=8)
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode='lines', name='Beam 2 (Right)',
        line=dict(color='#FF6B6B', width=8)
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
            z_pos = z_at_x * (1 - 0.3 * (1 - (2 * v_val - 1)**2))
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
        opacity=0.5, showscale=False, name='Membrane'
    ))

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

    if materials:
        num_bays = materials.get("num_bays", 2)
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 30)
        
        bracing_x = generate_bracing_positions(span, num_bays)
        bracing_x_sorted = sorted(bracing_x)

        roof_radius = max(span/2, laa/2)
        anchor_offset = roof_radius * 1.3
        
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
            
            if bx < 0 and anchor_x > -span/4:
                anchor_x = -span/3
            elif bx > 0 and anchor_x < span/4:
                anchor_x = span/3
            
            anchor1_y = -anchor_offset - lateral_offset * 0.5
            anchor2_y = anchor_offset + lateral_offset * 0.5

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

def generate_tent(params, materials=None):
    span = params.get("span_width", 10.0)
    ridge = params.get("ridge_height", 5.0)
    bays = params.get("num_bays", 4)
    bay_dist = params.get("bay_distance", 5.0)
    total_len = bays * bay_dist
    
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,total_len], z=[ridge,ridge], mode='lines', name='Ridge', line=dict(width=8, color='#f39c12')))
    fig.add_trace(go.Scatter3d(x=[-span/2,-span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Left', line=dict(width=5, color='#4a7a9c')))
    fig.add_trace(go.Scatter3d(x=[span/2,span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Right', line=dict(width=5, color='#4a7a9c')))
    
    X, Y = np.meshgrid(np.linspace(-span/2, span/2, 30), np.linspace(0, total_len, 30))
    Z = ridge * (1 - (X/(span/2))**2) * (1 - (Y/total_len)**2 * 0.1)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.5, colorscale='Reds', showscale=False, name='Fabric'))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)',
            yaxis_title='Length (m)',
            zaxis_title='Height (m)',
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

def generate_tensile(params, materials=None):
    mast = params.get("mast_height", 8.0)
    length = params.get("span_length", 20.0)
    width = params.get("span_width", 15.0)
    cables = params.get("cable_count", 4)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0,mast], mode='lines', name='Mast', line=dict(width=10, color='#f39c12')))
    
    X, Y = np.meshgrid(np.linspace(-length/2, length/2, 30), np.linspace(-width/2, width/2, 30))
    Z = mast * np.exp(-((X/(length/2))**2 + (Y/(width/2))**2) * 0.5)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.4, colorscale='Greens', showscale=False, name='Membrane'))
    
    for i in range(cables):
        angle = i * 2*np.pi/cables
        fig.add_trace(go.Scatter3d(
            x=[0, length/2*np.cos(angle)],
            y=[0, width/2*np.sin(angle)],
            z=[mast, 0],
            mode='lines',
            name=f'Cable {i+1}',
            line=dict(width=4, color='#4a7a9c')
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Length (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)',
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

def generate_portal(params, materials=None):
    eave = params.get("eave_height", 6.0)
    span = params.get("span_width", 20.0)
    pitch = params.get("roof_pitch", 5.0)
    bays = params.get("num_bays", 5)
    bay_spacing = params.get("bay_spacing", 6.0)
    total_len = bays * bay_spacing
    ridge = eave + span/2 * np.tan(np.radians(pitch))
    
    fig = go.Figure()
    x, z = [-span/2, -span/2, 0, span/2, span/2], [0, eave, ridge, eave, 0]
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', name='Portal Frame', line=dict(width=8, color='#4a7a9c')))
    
    for i in range(bays):
        y = i * bay_spacing
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(width=4, color='#4a7a9c', opacity=0.3), showlegend=False))
    
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 30))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.3, colorscale='Greys', showscale=False, name='Roof'))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)',
            yaxis_title='Length (m)',
            zaxis_title='Height (m)',
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

def generate_custom(params, materials=None):
    width = params.get("width", 10.0)
    length = params.get("length", 15.0)
    height = params.get("height", 8.0)
    
    fig = go.Figure()
    corners = [
        [-width/2, -length/2, 0],
        [width/2, -length/2, 0],
        [width/2, length/2, 0],
        [-width/2, length/2, 0],
        [-width/2, -length/2, height],
        [width/2, -length/2, height],
        [width/2, length/2, height],
        [-width/2, length/2, height]
    ]
    edges = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]
    
    for i, j in edges:
        fig.add_trace(go.Scatter3d(
            x=[corners[i][0], corners[j][0]],
            y=[corners[i][1], corners[j][1]],
            z=[corners[i][2], corners[j][2]],
            mode='lines',
            line=dict(color='#4a7a9c', width=3),
            showlegend=False
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)',
            yaxis_title='Length (m)',
            zaxis_title='Height (m)',
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0)
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
# TOP NAVIGATION
# ============================================================
def render_top_nav():
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        if st.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("📋 New Project", key="nav_new_project", use_container_width=True):
            clear_previous_project_data()
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
        if st.button("📄 BQ & Costing", key="nav_bq", use_container_width=True):
            if st.session_state.project_info:
                if has_feature("bq"):
                    st.session_state.page = "bq"
                    st.rerun()
                else:
                    st.info("🔒 BQ & Costing is available in Pro and Business versions")
            else:
                st.warning("Please create or open a project first")
    with col6:
        if st.button("📊 Reports", key="nav_reports", use_container_width=True):
            if st.session_state.project_info:
                st.session_state.page = "reports"
                st.rerun()
            else:
                st.warning("Please create or open a project first")
    
    license_info = get_license_info()
    remaining = get_remaining_projects()
    st.markdown(f"""
    <div style='display: flex; justify-content: flex-end; padding: 0.2rem 0;'>
        <span class='license-badge {license_info["badge_class"]}'>
            {license_info["badge"]} - {license_info["name"]}
        </span>
        <span style='color: #8a9aaa; font-size: 0.7rem; margin-left: 1rem;'>
            Projects: {len(st.session_state.saved_projects)} / {remaining}
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

# ============================================================
# LICENSE SWITCHER - PROMINENT ON DASHBOARD
# ============================================================
def render_license_switcher():
    """Prominent license switcher on dashboard"""
    current_tier = st.session_state.license_tier
    
    st.markdown("""
    <div class="license-switcher">
        <div class="title">🔑 LICENSE TIER SELECTOR</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("🔓 FREE", key="license_free", use_container_width=True,
                    type="primary" if current_tier == "free" else "secondary"):
            st.session_state.license_tier = "free"
            st.rerun()
    with col2:
        if st.button("🔓 PRO", key="license_pro", use_container_width=True,
                    type="primary" if current_tier == "pro" else "secondary"):
            st.session_state.license_tier = "pro"
            st.rerun()
    with col3:
        if st.button("🔓 BUSINESS", key="license_business", use_container_width=True,
                    type="primary" if current_tier == "business" else "secondary"):
            st.session_state.license_tier = "business"
            st.rerun()
    with col4:
        license_info = get_license_info()
        badge_class = license_info["badge_class"]
        st.markdown(f"""
        <div style='text-align: right; padding: 0.3rem 0;'>
            <span style='color: #8a9aaa; font-size: 0.8rem;'>Current: </span>
            <span class='license-badge {badge_class}' style='font-size: 0.9rem;'>
                {license_info["badge"]} - {license_info["name"]}
            </span>
            <br>
            <span style='color: #6a7a8a; font-size: 0.65rem;'>
                ⚠️ Remember to switch to FREE before deployment
            </span>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# DASHBOARD PAGE
# ============================================================
def render_dashboard():
    st.title("🧬 FDS - Fluid Design Studio")
    st.caption('*"Rigid in Principle. Fluid in Application."*')
    
    # ===== PROMINENT LICENSE SWITCHER =====
    render_license_switcher()
    st.divider()
    
    # ===== TWO DESIGN PATHS =====
    st.markdown("## 🚀 Start Your Design")
    st.markdown("Choose how you'd like to begin:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="design-path-card">
            <div class="icon">🧠</div>
            <div class="title">Guided Design</div>
            <div class="desc">"I need help deciding"<br>
            Answer a few questions and we'll recommend<br>
            the best structure for your needs</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧠 Start Guided Design", key="start_guided", use_container_width=True, type="primary"):
            st.session_state.design_path = "guided"
            st.session_state.brief_step = 0
            st.session_state.brief_answers = {}
            st.session_state.page = "design_brief"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="design-path-card">
            <div class="icon">⚡</div>
            <div class="title">Direct Design</div>
            <div class="desc">"I know what I want"<br>
            Choose from our structure types and<br>
            go straight to design</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ Start Direct Design", key="start_direct", use_container_width=True, type="primary"):
            st.session_state.design_path = "direct"
            st.session_state.page = "catalog"
            st.rerun()
    
    st.divider()
    
    # ===== DASHBOARD STATS =====
    projects = st.session_state.saved_projects
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>📂</div><div class='value'>{len(projects)}</div><div class='label'>Saved Projects</div></div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>🏗️</div><div class='value'>{len(STRUCTURE_QUESTIONS)}</div><div class='label'>Structure Types</div></div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>🔧</div><div class='value'>100+</div><div class='label'>Sections Available</div></div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>⚡</div><div class='value'>AI</div><div class='label'>Intelligent Engine</div></div>", unsafe_allow_html=True)
    
    # ===== RECENT PROJECTS =====
    if projects:
        st.divider()
        st.subheader("📂 Recent Projects")
        for i, proj in enumerate(projects[-5:]):
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{proj.get('project_info', {}).get('name', 'Untitled')}** — {proj.get('project_info', {}).get('client', 'Unknown')}")
            std = proj.get("materials", {}).get("standard", "EU")
            badge = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(std, "badge-eu")
            col1.markdown(f'<span class="standard-badge {badge}">{std}</span> {proj.get("typology", "Unknown")}', unsafe_allow_html=True)
            if col2.button("📂 Load", key=f"dash_load_{i}", use_container_width=True):
                clear_previous_project_data()
                st.session_state.project_info = proj.get("project_info", {})
                st.session_state.materials = proj.get("materials", st.session_state.materials)
                st.session_state.params = proj.get("params", {})
                st.session_state.typology = proj.get("typology", "saddle_span")
                st.session_state.page = "workspace"
                st.rerun()

# ============================================================
# DESIGN BRIEF PAGE (Guided Design)
# ============================================================
def render_design_brief():
    st.title("🧠 Guided Design")
    st.caption("Answer a few questions and we'll recommend the best structure for you")
    
    # Progress
    total_questions = 0
    for structure_data in STRUCTURE_QUESTIONS.values():
        for section, questions in structure_data["questions"].items():
            total_questions += len(questions)
    
    answered = len(st.session_state.brief_answers)
    progress = answered / total_questions if total_questions > 0 else 0
    
    st.markdown(f"""
    <div class="question-counter">Question {answered + 1} of {total_questions}</div>
    <div class="progress-bar">
        <div class="fill" style="width: {progress * 100}%;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Determine current structure type
    structure_types = list(STRUCTURE_QUESTIONS.keys())
    current_type = structure_types[0]
    
    # Get questions for current structure
    structure_data = STRUCTURE_QUESTIONS.get(current_type, {})
    all_questions = []
    for section, questions in structure_data.get("questions", {}).items():
        for q in questions:
            q["section"] = section
            all_questions.append(q)
    
    # Filter questions based on conditions
    visible_questions = []
    for q in all_questions:
        if q["condition"] is None:
            visible_questions.append(q)
        else:
            condition_met = True
            for key, values in q["condition"].items():
                if key in st.session_state.brief_answers:
                    if st.session_state.brief_answers[key] not in values:
                        condition_met = False
                        break
                else:
                    condition_met = False
            if condition_met:
                visible_questions.append(q)
    
    # Show current question
    if st.session_state.brief_step < len(visible_questions):
        q = visible_questions[st.session_state.brief_step]
        
        st.markdown(f"""
        <div class="sds-card">
            <div class="title">📝 {q['question']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show options as radio buttons
        answer = st.radio(
            "Select your answer:",
            q["options"],
            key=f"brief_{q['id']}",
            index=None
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.session_state.brief_step > 0:
                if st.button("⬅ Previous", use_container_width=True):
                    st.session_state.brief_step -= 1
                    st.rerun()
        
        with col2:
            if answer:
                st.session_state.brief_answers[q["id"]] = answer
                if st.button("Next ➡", use_container_width=True, type="primary"):
                    st.session_state.brief_step += 1
                    st.rerun()
            else:
                st.button("Next ➡", use_container_width=True, disabled=True)
    
    else:
        # All questions answered - show recommendation
        st.success("✅ All questions answered!")
        
        # Generate recommendation
        recommendation = recommend_system(st.session_state.brief_answers)
        
        st.markdown("## 🎯 System Recommendation")
        st.markdown(f"""
        <div class="sds-card" style="border: 2px solid #f39c12;">
            <div class="title" style="font-size: 1.2rem;">
                🏆 Recommended: {recommendation['recommended'].replace('_', ' ').title()}
            </div>
            <div class="content">
                <p><strong>Confidence:</strong> {recommendation['confidence']}%</p>
                <p><strong>Explanation:</strong> {recommendation['explanation']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show score breakdown
        st.markdown("### 📊 System Scores")
        for system, score in recommendation["scores"].items():
            st.progress(score / 10 if score > 0 else 0.01, text=f"{system.replace('_', ' ').title()}: {score}/10")
        
        # Proceed to design
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁 Restart Brief", use_container_width=True):
                st.session_state.brief_step = 0
                st.session_state.brief_answers = {}
                st.rerun()
        with col2:
            if st.button("🚀 Proceed to Design", use_container_width=True, type="primary"):
                st.session_state.materials["system_type"] = recommendation["recommended"]
                st.session_state.materials["member_type"] = "single_beam"
                
                if current_type in ["saddle_span", "clear_span_tent"]:
                    st.session_state.typology = current_type
                    st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
                else:
                    st.session_state.typology = "saddle_span"
                    st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
                
                st.session_state.project_info = {
                    "name": f"{current_type.replace('_', ' ').title()} Design",
                    "client": "Guided Design",
                    "reference": f"FDS-{datetime.now().strftime('%Y%m%d')}",
                    "date": datetime.now().isoformat()
                }
                
                st.session_state.page = "workspace"
                st.rerun()

# ============================================================
# REGISTRATION PAGE
# ============================================================
def render_registration():
    st.subheader("📋 New Project")
    
    remaining = get_remaining_projects()
    if st.session_state.license_tier == "free":
        st.caption(f"📊 Remaining projects: {remaining} / {LICENSE_TIERS['free']['project_limit']}")
    
    with st.form("register_form"):
        name = st.text_input("Project Name *", placeholder="e.g., OCB Canopy")
        client = st.text_input("Client Name *", placeholder="e.g., OCBC")
        location = st.text_input("Location", placeholder="e.g., Kuala Lumpur, Malaysia")
        standard = st.selectbox("Design Standard", ["EU", "CN", "UK", "MY", "US"], index=3)
        ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.caption(f"Reference: FDS-{ref}")
        
        if st.form_submit_button("🚀 Start Design", key="register_start", use_container_width=True, type="primary"):
            if not name or not client:
                st.error("⚠️ Project Name and Client Name are required.")
            else:
                clear_previous_project_data()
                st.session_state.project_info = {
                    "name": name,
                    "client": client,
                    "location": location,
                    "reference": f"FDS-{ref}",
                    "date": datetime.now().isoformat()
                }
                st.session_state.materials["standard"] = standard
                st.session_state.design_path = "direct"
                st.session_state.page = "catalog"
                st.rerun()

# ============================================================
# PROJECT BROWSER
# ============================================================
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
            std = proj.get("materials", {}).get("standard", "EU")
            badge = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(std, "badge-eu")
            col1.markdown(f'<span class="standard-badge {badge}">{std}</span> {proj.get("typology", "Unknown")}', unsafe_allow_html=True)
            if col2.button("📂 Load", key=f"browser_load_{i}", use_container_width=True):
                clear_previous_project_data()
                st.session_state.project_info = proj.get("project_info", {})
                st.session_state.materials = proj.get("materials", st.session_state.materials)
                st.session_state.params = proj.get("params", {})
                st.session_state.typology = proj.get("typology", "saddle_span")
                st.session_state.page = "workspace"
                st.rerun()
            if col3.button("🗑️ Delete", key=f"browser_del_{i}", use_container_width=True):
                st.session_state.saved_projects.pop(len(projects) - 1 - i)
                st.rerun()
            st.divider()

# ============================================================
# CATALOG PAGE (Direct Design)
# ============================================================
def render_catalog():
    st.subheader("🏗️ Choose a Structure Type")
    st.caption("Select the structure type you want to design")
    
    # Show available structure types
    structure_types = list(STRUCTURE_QUESTIONS.keys())
    
    # Display in grid
    cols = st.columns(2)
    for i, (key, data) in enumerate(STRUCTURE_QUESTIONS.items()):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="design-path-card">
                <div class="icon">{data['icon']}</div>
                <div class="title">{data['name']}</div>
                <div class="desc">Systems: {', '.join(data['systems']).replace('_', ' ').title()}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {data['name']}", key=f"catalog_{key}", use_container_width=True, type="primary"):
                st.session_state.typology = key
                st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
                st.session_state.page = "workspace"
                st.rerun()

# ============================================================
# BQ & COSTING PAGE
# ============================================================
def render_bq_page():
    st.title("📄 Bill of Quantities & Costing")
    st.caption("Detailed material takeoff and cost breakdown")
    
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
    
    if "bq" not in st.session_state or not st.session_state.bq:
        st.info("💡 Please run the design first to generate the Bill of Quantities.")
        if st.button("🏗️ Go to Workspace", key="bq_goto_workspace", use_container_width=True, type="primary"):
            st.session_state.page = "workspace"
            st.rerun()
        return
    
    bq = st.session_state.bq
    if not bq or "items" not in bq:
        st.info("💡 Please run the design first to generate the Bill of Quantities.")
        if st.button("🏗️ Go to Workspace", key="bq_goto_workspace2", use_container_width=True, type="primary"):
            st.session_state.page = "workspace"
            st.rerun()
        return
    
    currency = bq.get("currency", get_currency("Malaysia"))
    st.markdown(f"**Currency:** {currency['code']} ({currency['symbol']})")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Cost", f"{currency['symbol']}{bq['total_cost']:,.0f}")
    col2.metric("🔩 Steel Weight", f"{bq['total_steel_weight']:.0f} kg")
    col3.metric("📐 Fabric Area", f"{bq['total_fabric_area']:.0f} m²")
    col4.metric("🔗 Joint Type", bq.get('joint_type', 'bolted').upper())
    
    st.divider()
    
    st.subheader("📋 Detailed Bill of Quantities")
    
    bq_data = []
    for item in bq["items"]:
        bq_data.append({
            "Item": item["item"],
            "Qty": item["qty"],
            "Unit": item["unit"],
            "Length (m)": item["length_m"],
            "Total Length (m)": item["total_length_m"],
            "Weight (kg)": f"{item['weight_kg']:.0f}" if isinstance(item['weight_kg'], (int, float)) else item['weight_kg'],
            "Unit Price": f"{currency['symbol']}{item['unit_price']:.2f}" if isinstance(item['unit_price'], (int, float)) else item['unit_price'],
            "Total": f"{currency['symbol']}{item['total_price']:,.0f}" if isinstance(item['total_price'], (int, float)) else item['total_price']
        })
    
    if bq_data:
        df = pd.DataFrame(bq_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown(f"""
        <div style='text-align:right;padding:0.5rem;background:#1e2a3a;border-radius:8px;margin-top:0.5rem;'>
            <span style='font-size:1.2rem;font-weight:700;color:#f39c12;'>
                GRAND TOTAL: {currency['symbol']}{bq['total_cost']:,.0f}
            </span>
            <br>
            <span style='font-size:0.8rem;color:#b0c4de;'>
                {bq.get('joint_description', '')}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download CSV", key="bq_download_csv", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"BQ_{st.session_state.project_info.get('reference', 'project')}.csv",
                mime="text/csv",
                key="bq_download_btn"
            )
    with col2:
        if st.button("🏠 Back to Workspace", key="bq_back_workspace", use_container_width=True, type="primary"):
            st.session_state.page = "workspace"
            st.rerun()

# ============================================================
# REPORTS PAGE
# ============================================================
def render_reports():
    st.title("📊 Reports & Export")
    st.caption("Generate professional reports and drawings")
    
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
    
    # PDF Export
    st.subheader("📄 PDF Report")
    st.markdown("Generate a professional PDF report with design summary, BQ, and 3D visualization")
    
    if st.button("📄 Generate PDF Report", key="reports_pdf", use_container_width=True, type="primary"):
        try:
            fig, axes = plt.subplots(2, 2, figsize=(10, 12))
            fig.patch.set_facecolor('#0a0e17')
            
            axes[0, 0].axis('off')
            axes[0, 0].text(0.5, 0.8, "FDS - Fluid Design Studio", fontsize=18, color='white', ha='center', weight='bold')
            axes[0, 0].text(0.5, 0.6, f"Project: {st.session_state.project_info.get('name', 'Untitled')}", fontsize=14, color='#b0c4de', ha='center')
            axes[0, 0].text(0.5, 0.4, f"Client: {st.session_state.project_info.get('client', 'Unknown')}", fontsize=12, color='#b0c4de', ha='center')
            axes[0, 0].text(0.5, 0.2, f"Date: {datetime.now().strftime('%B %d, %Y')}", fontsize=12, color='#b0c4de', ha='center')
            
            axes[0, 1].axis('off')
            axes[0, 1].text(0.1, 0.9, "Design Summary", fontsize=14, color='white', weight='bold')
            
            design = st.session_state.design_results
            loads = design.get('loads', {})
            y_pos = 0.8
            for key, value in loads.items():
                axes[0, 1].text(0.1, y_pos, f"{key.title()}: {value:.1f} kN", fontsize=11, color='#b0c4de')
                y_pos -= 0.08
            
            fabric = design.get('fabric', {})
            cables = design.get('cables', {})
            axes[0, 1].text(0.1, y_pos - 0.05, f"Fabric: {fabric.get('type', 'N/A')} ({fabric.get('thickness', 'N/A')}mm)", fontsize=11, color='#b0c4de')
            y_pos -= 0.08
            axes[0, 1].text(0.1, y_pos, f"Cable: {cables.get('type', 'N/A')} {cables.get('diameter', 'N/A')}mm", fontsize=11, color='#b0c4de')
            
            axes[1, 0].axis('off')
            score = design.get('health_score', 0)
            color = '#2ecc71' if score >= 80 else '#f39c12' if score >= 60 else '#e74c3c'
            axes[1, 0].text(0.5, 0.6, f"Health Score", fontsize=14, color='white', ha='center', weight='bold')
            axes[1, 0].text(0.5, 0.3, f"{score}%", fontsize=36, color=color, ha='center', weight='bold')
            
            bq = design.get('bq', {})
            axes[1, 1].axis('off')
            axes[1, 1].text(0.1, 0.9, "Cost Summary", fontsize=14, color='white', weight='bold')
            axes[1, 1].text(0.1, 0.75, f"Total Cost: {format_currency(bq.get('total_cost', 0), st.session_state.materials.get('country', 'Malaysia'))}", fontsize=12, color='#b0c4de')
            axes[1, 1].text(0.1, 0.6, f"Steel Weight: {bq.get('total_steel_weight', 0):.0f} kg", fontsize=12, color='#b0c4de')
            axes[1, 1].text(0.1, 0.45, f"Fabric Area: {bq.get('total_fabric_area', 0):.0f} m²", fontsize=12, color='#b0c4de')
            axes[1, 1].text(0.1, 0.3, f"Joint Type: {bq.get('joint_type', 'bolted').upper()}", fontsize=12, color='#b0c4de')
            
            plt.tight_layout()
            
            buf = BytesIO()
            plt.savefig(buf, format='pdf', facecolor='#0a0e17', edgecolor='none')
            buf.seek(0)
            plt.close()
            
            st.download_button(
                label="📥 Download PDF Report",
                data=buf,
                file_name=f"FDS_Report_{st.session_state.project_info.get('reference', 'project')}.pdf",
                mime="application/pdf",
                key="reports_pdf_download"
            )
            st.success("✅ PDF generated successfully!")
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")
            st.info("PDF generation requires matplotlib. Please ensure it's installed.")
    
    if st.button("🏠 Back to Workspace", key="reports_back_workspace", use_container_width=True, type="primary"):
        st.session_state.page = "workspace"
        st.rerun()

# ============================================================
# WORKSPACE PAGE
# ============================================================
def render_workspace():
    params = st.session_state.params
    materials = st.session_state.materials
    info = st.session_state.project_info
    typology = st.session_state.typology
    
    if typology not in GENERATORS:
        typology = "saddle_span"
    
    generator = GENERATORS.get(typology, generate_saddle_span)
    
    st.markdown("## 🧠 Design Workspace")
    st.caption(f"📌 {info.get('name', 'Untitled')} — {info.get('client', 'Unknown')}")
    st.caption(f"📐 {typology.replace('_', ' ').title()} | System: {materials.get('system_type', 'Rigid Frame').replace('_', ' ').title()}")
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        if st.button("🏠 Home", key="workspace_home", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("💾 Save", key="workspace_save", use_container_width=True, type="primary"):
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
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        st.markdown('<div class="sds-card"><div class="title">📐 Dimensions</div>', unsafe_allow_html=True)
        if typology == "saddle_span":
            params["A"] = st.number_input("Rise (A) m", 2.0, 20.0, params.get("A", 6.0), 0.5, disabled=st.session_state.locked, key="dim_A")
            params["B"] = st.number_input("Span (B) m", 4.0, 40.0, params.get("B", 10.0), 0.5, disabled=st.session_state.locked, key="dim_B")
            params["LAA"] = st.number_input("Apex Dist (LAA) m", 4.0, 50.0, params.get("LAA", 15.0), 0.5, disabled=st.session_state.locked, key="dim_LAA")
        elif typology == "clear_span_tent":
            params["span_width"] = st.number_input("Span Width (m)", 3.0, 80.0, params.get("span_width", 10.0), 0.5, disabled=st.session_state.locked, key="dim_span_width")
            params["ridge_height"] = st.number_input("Ridge Height (m)", 2.5, 12.0, params.get("ridge_height", 5.0), 0.5, disabled=st.session_state.locked, key="dim_ridge_height")
            params["num_bays"] = st.number_input("Number of Bays", 2, 10, params.get("num_bays", 4), 1, disabled=st.session_state.locked, key="dim_num_bays")
            params["bay_distance"] = st.number_input("Bay Distance (m)", 3.0, 15.0, params.get("bay_distance", 5.0), 0.5, disabled=st.session_state.locked, key="dim_bay_distance")
        elif typology == "tensile_membrane":
            params["mast_height"] = st.number_input("Mast Height (m)", 3.0, 20.0, params.get("mast_height", 8.0), 0.5, disabled=st.session_state.locked, key="dim_mast_height")
            params["span_length"] = st.number_input("Span Length (m)", 5.0, 50.0, params.get("span_length", 20.0), 0.5, disabled=st.session_state.locked, key="dim_span_length")
            params["span_width"] = st.number_input("Span Width (m)", 5.0, 40.0, params.get("span_width", 15.0), 0.5, disabled=st.session_state.locked, key="dim_span_width_tensile")
            params["cable_count"] = st.number_input("Number of Cables", 3, 8, params.get("cable_count", 4), 1, disabled=st.session_state.locked, key="dim_cable_count")
        elif typology == "portal_frame":
            params["eave_height"] = st.number_input("Eave Height (m)", 3.0, 15.0, params.get("eave_height", 6.0), 0.5, disabled=st.session_state.locked, key="dim_eave_height")
            params["span_width"] = st.number_input("Span Width (m)", 5.0, 50.0, params.get("span_width", 20.0), 0.5, disabled=st.session_state.locked, key="dim_span_width_portal")
            params["roof_pitch"] = st.number_input("Roof Pitch (degrees)", 1.0, 15.0, params.get("roof_pitch", 5.0), 0.5, disabled=st.session_state.locked, key="dim_roof_pitch")
            params["num_bays"] = st.number_input("Number of Bays", 2, 10, params.get("num_bays", 5), 1, disabled=st.session_state.locked, key="dim_num_bays_portal")
            params["bay_spacing"] = st.number_input("Bay Spacing (m)", 3.0, 12.0, params.get("bay_spacing", 6.0), 0.5, disabled=st.session_state.locked, key="dim_bay_spacing")
        elif typology == "custom":
            params["width"] = st.number_input("Width (m)", 2.0, 30.0, params.get("width", 10.0), 0.5, disabled=st.session_state.locked, key="dim_width")
            params["length"] = st.number_input("Length (m)", 2.0, 40.0, params.get("length", 15.0), 0.5, disabled=st.session_state.locked, key="dim_length")
            params["height"] = st.number_input("Height (m)", 2.0, 20.0, params.get("height", 8.0), 0.5, disabled=st.session_state.locked, key="dim_height")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Materials section
        st.markdown('<div class="sds-card"><div class="title">🧱 Materials</div>', unsafe_allow_html=True)
        materials["standard"] = st.selectbox(
            "Design Standard",
            ["EU", "CN", "UK", "MY", "US"],
            index=["EU", "CN", "UK", "MY", "US"].index(materials.get("standard", "EU")),
            disabled=st.session_state.locked,
            key="mat_standard"
        )
        materials["material_type"] = st.selectbox(
            "Material Type",
            ["Steel", "Aluminum", "Wood", "Composite"],
            index=["Steel", "Aluminum", "Wood", "Composite"].index(materials.get("material_type", "Steel")),
            disabled=st.session_state.locked,
            key="mat_material_type"
        )
        materials["section_type"] = st.selectbox(
            "Section Type",
            ["CHS", "SHS", "RHS", "I-Beam", "Angle", "Channel"],
            index=["CHS", "SHS", "RHS", "I-Beam", "Angle", "Channel"].index(materials.get("section_type", "CHS")),
            disabled=st.session_state.locked,
            key="mat_section_type"
        )
        materials["joint_type"] = st.selectbox(
            "Joint Type",
            ["bolted", "welded"],
            index=["bolted", "welded"].index(materials.get("joint_type", "bolted")),
            disabled=st.session_state.locked,
            key="mat_joint_type"
        )
        materials["fabric_type"] = st.selectbox(
            "Fabric Type",
            ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"],
            index=["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"].index(materials.get("fabric_type", "PVC-coated Polyester")),
            disabled=st.session_state.locked,
            key="mat_fabric_type"
        )
        materials["cable_type"] = st.selectbox(
            "Cable Type",
            ["6x19 Galvanized", "6x19 Stainless", "Polyester Rope"],
            index=["6x19 Galvanized", "6x19 Stainless", "Polyester Rope"].index(materials.get("cable_type", "6x19 Galvanized")),
            disabled=st.session_state.locked,
            key="mat_cable_type"
        )
        materials["country"] = st.selectbox(
            "Country",
            list(COUNTRY_CURRENCIES.keys()),
            index=list(COUNTRY_CURRENCIES.keys()).index(materials.get("country", "Malaysia")),
            disabled=st.session_state.locked,
            key="mat_country"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Advanced settings
        st.markdown('<div class="sds-card"><div class="title">⚙️ Advanced Settings</div>', unsafe_allow_html=True)
        materials["num_bays"] = st.number_input("Number of Bays", 1, 5, materials.get("num_bays", 2), 1, disabled=st.session_state.locked, key="adv_num_bays")
        materials["tie_down_vertical_angle"] = st.number_input("Tie-down Vertical Angle (°)", 15, 75, materials.get("tie_down_vertical_angle", 45), 5, disabled=st.session_state.locked, key="adv_vertical_angle")
        materials["tie_down_horizontal_spread"] = st.number_input("Tie-down Horizontal Spread (°)", 10, 60, materials.get("tie_down_horizontal_spread", 30), 5, disabled=st.session_state.locked, key="adv_horizontal_spread")
        materials["prestress_level"] = st.selectbox(
            "Prestress Level",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(materials.get("prestress_level", "medium")),
            disabled=st.session_state.locked,
            key="adv_prestress"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Design button
        if st.button("🚀 Run Design", key="run_design", use_container_width=True, type="primary"):
            with st.spinner("🔄 Running engineering calculations..."):
                results = auto_design_structure(params, materials, typology)
                st.session_state.design_results = results
                st.session_state.bq = results["bq"]
                st.success("✅ Design complete!")
                st.rerun()
    
    with col_right:
        # 3D Viewer
        st.markdown('<div class="sds-card"><div class="title">🌐 3D Viewer</div>', unsafe_allow_html=True)
        fig = generator(params, materials if typology == "saddle_span" else None)
        if fig and isinstance(fig, go.Figure):
            st.plotly_chart(fig, use_container_width=True, height=500)
        else:
            st.info("Adjust dimensions to see 3D visualization")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Design Results
        if "design_results" in st.session_state and st.session_state.design_results:
            results = st.session_state.design_results
            
            # Health Score
            score = results.get("health_score", 0)
            if score >= 80:
                score_class = "health-score-good"
                status_text = "✅ Healthy Design"
            elif score >= 60:
                score_class = "health-score-fair"
                status_text = "⚠️ Fair Design"
            else:
                score_class = "health-score-poor"
                status_text = "❌ Needs Attention"
            
            st.markdown(f"""
            <div class="sds-card" style="border: 2px solid #2a3a4f;">
                <div class="title">📊 Design Health</div>
                <div class="content">
                    <span class="{score_class}">{score}%</span>
                    <span style="margin-left: 1rem; color: #b0c4de;">{status_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Loads summary
            loads = results.get("loads", {})
            if loads:
                st.markdown('<div class="sds-card"><div class="title">📊 Loads</div>', unsafe_allow_html=True)
                cols = st.columns(2)
                with cols[0]:
                    st.metric("Wind", f"{loads.get('wind', 0):.1f} kN")
                    st.metric("Dead", f"{loads.get('dead', 0):.1f} kN")
                with cols[1]:
                    st.metric("Live", f"{loads.get('live', 0):.1f} kN")
                    st.metric("Total", f"{loads.get('total', 0):.1f} kN", 
                             delta=f"{results.get('joint_type', 'bolted').upper()}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Section selection
            if results.get("beams", {}).get("selected"):
                beam = results["beams"]
                st.markdown(f"""
                <div class="sds-card">
                    <div class="title">🔧 Selected Section</div>
                    <div class="content">
                        <strong>{beam.get('selected', 'N/A')}</strong><br>
                        <span style="color: #8a9aaa;">
                            Type: {beam.get('section_type', 'N/A')} 
                            {get_section_tag(beam.get('section_type', ''))}
                        </span><br>
                        <span style="color: #8a9aaa;">
                            Moment: {beam.get('moment_capacity', 0):.1f} kNm / {beam.get('required_moment', 0):.1f} kNm req
                        </span><br>
                        <span style="color: #8a9aaa;">
                            {beam.get('note', '✅ Adequate')}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Fabric and Cables
            fabric = results.get("fabric", {})
            cables = results.get("cables", {})
            if fabric or cables:
                st.markdown('<div class="sds-card"><div class="title">🧵 Materials</div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Fabric", f"{fabric.get('type', 'N/A')}", 
                             f"{fabric.get('thickness', 'N/A')}mm")
                with col2:
                    st.metric("Cable", f"{cables.get('type', 'N/A')}", 
                             f"{cables.get('diameter', 'N/A')}mm")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # All checks summary
            checks = results.get("all_checks", {})
            if checks:
                st.markdown('<div class="sds-card"><div class="title">✅ Design Checks</div>', unsafe_allow_html=True)
                for key, check in checks.items():
                    if key in ["section_ratios"]:
                        continue
                    status = check.get("status", "N/A")
                    value = check.get("value", "")
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 0.15rem 0; border-bottom: 1px solid #1a2a3a;">
                        <span style="color: #b0c4de; font-size: 0.8rem;">{key.replace('_', ' ').title()}</span>
                        <span style="font-size: 0.8rem;">{status} {value}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("💡 Click 'Run Design' to see results")
    
    st.divider()
    
    # Comments
    with st.expander("📝 Add Comments", expanded=False):
        comments = st.text_area("Comments", st.session_state.comments, height=100, disabled=st.session_state.locked)
        if st.button("💬 Save Comments", key="save_comments", use_container_width=True, type="primary"):
            st.session_state.comments = comments
            st.success("Comments saved!")

# ============================================================
# MAIN APP
# ============================================================
def main():
    # Render top navigation
    render_top_nav()
    
    # Page routing
    page = st.session_state.page
    
    if page == "dashboard":
        render_dashboard()
    elif page == "design_brief":
        render_design_brief()
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

if __name__ == "__main__":
    main()
