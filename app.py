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
import zipfile

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SDSe - Intelligent Fluid Design Workplace",
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
    .stRadio > div label[data-checked="true"] {
        color: #f39c12 !important;
        border-color: #f39c12 !important;
        background-color: rgba(243, 156, 18, 0.1) !important;
        font-weight: 600 !important;
    }
    .stRadio > div label[data-checked="true"]:hover {
        border-color: #f1c40f !important;
        color: #f1c40f !important;
    }
    .stRadio > div label div[data-testid="stMarkdownContainer"] {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .stRadio > div label div[data-testid="stMarkdownContainer"] > div:first-child {
        width: 14px !important;
        height: 14px !important;
        border-radius: 50% !important;
        border: 2px solid #4a5a6a !important;
        transition: all 0.3s ease !important;
        flex-shrink: 0 !important;
    }
    .stRadio > div label[data-checked="true"] div[data-testid="stMarkdownContainer"] > div:first-child {
        border-color: #f39c12 !important;
        background-color: #f39c12 !important;
        box-shadow: 0 0 8px rgba(243, 156, 18, 0.4) !important;
    }
    .stRadio > div label[data-checked="true"] div[data-testid="stMarkdownContainer"] > div:first-child::after {
        content: "" !important;
        display: block !important;
        width: 6px !important;
        height: 6px !important;
        border-radius: 50% !important;
        background-color: #0a0e17 !important;
        margin: 2px auto !important;
    }
    
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
    
    .export-btn {
        background-color: #2a3a4f !important;
        border: 1px solid #4a7a9c !important;
        color: #ffffff !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }
    .export-btn:hover {
        background-color: #3a4a5f !important;
        border-color: #6a9abc !important;
    }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# ALL FEATURES ARE FREE
# ============================================================
def has_feature(feature_name):
    return True

def get_license_info():
    return {"name": "SDSe", "badge": "FREE", "badge_class": "license-free"}

def check_project_limit():
    return True

def get_remaining_projects():
    return "Unlimited"

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
            "dome_height": 20
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
        "dome_height": 20
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
# ENHANCED STRUCTURE TYPES - 25 STRUCTURES
# ============================================================
STRUCTURE_TYPES = {
    # TENSILE STRUCTURES
    "saddle_span": {"name": "Saddle Span", "icon": "🏕️", "description": "Curved saddle-shaped tensile structure", "category": "Tensile"},
    "clear_span_tent": {"name": "Clear-Span Tent", "icon": "🏗️", "description": "Column-free tensile tent structure", "category": "Tensile"},
    "tensile_membrane": {"name": "Tensile Membrane", "icon": "⛺", "description": "Tensioned fabric membrane structure", "category": "Tensile"},
    "cable_net": {"name": "Cable Net", "icon": "🕸️", "description": "Interconnected cable grid structure", "category": "Tensile"},
    "cable_stayed": {"name": "Cable-Stayed", "icon": "🗼", "description": "Cable-supported tensile structure", "category": "Tensile"},
    "mast_supported": {"name": "Mast Supported", "icon": "🚩", "description": "Central mast with tensioned membrane", "category": "Tensile"},
    "stress_ribbon": {"name": "Stress Ribbon", "icon": "🎀", "description": "Tensioned ribbon bridge structure", "category": "Tensile"},
    "inflatable_structure": {"name": "Inflatable Structure", "icon": "🎈", "description": "Air-supported membrane structure", "category": "Tensile"},
    
    # FRAME STRUCTURES
    "portal_frame": {"name": "Portal Frame", "icon": "🏛️", "description": "Rigid steel frame structure", "category": "Frame"},
    "arch_structure": {"name": "Arch Structure", "icon": "🌉", "description": "Curved arch supporting structure", "category": "Frame"},
    "frame_system": {"name": "Frame System", "icon": "🏗️", "description": "Traditional frame structure", "category": "Frame"},
    "fabricated_beam": {"name": "Fabricated Beam", "icon": "📏", "description": "Custom fabricated beam structure", "category": "Frame"},
    "shell_structure": {"name": "Shell Structure", "icon": "🐚", "description": "Thin shell structural surface", "category": "Frame"},
    "folded_plate": {"name": "Folded Plate", "icon": "📐", "description": "Folded structural surface", "category": "Frame"},
    
    # SPATIAL STRUCTURES
    "geodesic_dome": {"name": "Geodesic Dome", "icon": "🌍", "description": "Spherical lattice shell structure", "category": "Spatial"},
    "space_frame": {"name": "Space Frame", "icon": "✧", "description": "3D truss network structure", "category": "Spatial"},
    "grid_shell": {"name": "Grid Shell", "icon": "🔷", "description": "Grid-based shell structure", "category": "Spatial"},
    "tensegrity": {"name": "Tensegrity", "icon": "🔮", "description": "Tension-integrity structure", "category": "Spatial"},
    "hybrid_system": {"name": "Hybrid System", "icon": "⚡", "description": "Combined structural systems", "category": "Spatial"},
    
    # SPECIALIZED STRUCTURES
    "retractable_roof": {"name": "Retractable Roof", "icon": "🔄", "description": "Opening and closing roof system", "category": "Specialized"},
    "suspension_bridge": {"name": "Suspension Bridge", "icon": "🌉", "description": "Cable-suspended bridge structure", "category": "Specialized"},
    "truss_system": {"name": "Truss System", "icon": "📐", "description": "Triangulated truss structure", "category": "Specialized"},
    "roof_system": {"name": "Roof System", "icon": "🏠", "description": "Comprehensive roof structure", "category": "Specialized"},
    "shade_structure": {"name": "Shade Structure", "icon": "🌴", "description": "Architectural shading system", "category": "Specialized"},
    "bridge_viaduct": {"name": "Bridge/Viaduct", "icon": "🌉", "description": "Structural bridge system", "category": "Specialized"}
}

# ============================================================
# STRUCTURE INPUT FORMS (Feature 2)
# ============================================================
def get_structure_input_form(typology, params, materials, locked):
    """Dynamic input form for each structure type"""
    
    st.markdown('<div class="sds-card"><div class="title">📐 Structure Parameters</div>', unsafe_allow_html=True)
    
    if typology == "saddle_span":
        params["A"] = st.number_input("Rise (A) m", 2.0, 20.0, params.get("A", 6.0), 0.5, disabled=locked, key="dim_A")
        params["B"] = st.number_input("Span (B) m", 4.0, 40.0, params.get("B", 10.0), 0.5, disabled=locked, key="dim_B")
        params["LAA"] = st.number_input("Apex Dist (LAA) m", 4.0, 50.0, params.get("LAA", 15.0), 0.5, disabled=locked, key="dim_LAA")
        
    elif typology == "clear_span_tent":
        params["span_width"] = st.number_input("Span Width (m)", 3.0, 80.0, params.get("span_width", 10.0), 0.5, disabled=locked, key="dim_span_width")
        params["ridge_height"] = st.number_input("Ridge Height (m)", 2.5, 12.0, params.get("ridge_height", 5.0), 0.5, disabled=locked, key="dim_ridge_height")
        params["bay_distance"] = st.number_input("Bay Distance (m)", 3.0, 10.0, params.get("bay_distance", 5.0), 0.5, disabled=locked, key="dim_bay_distance")
        params["num_bays"] = st.number_input("Number of Bays", 1, 20, params.get("num_bays", 4), 1, disabled=locked, key="dim_num_bays")
        
    elif typology == "tensile_membrane":
        params["mast_height"] = st.number_input("Mast Height (m)", 3.0, 30.0, params.get("mast_height", 8.0), 0.5, disabled=locked, key="dim_mast_height")
        params["span_length"] = st.number_input("Span Length (m)", 5.0, 100.0, params.get("span_length", 20.0), 0.5, disabled=locked, key="dim_span_length")
        params["span_width"] = st.number_input("Span Width (m)", 5.0, 80.0, params.get("span_width", 15.0), 0.5, disabled=locked, key="dim_tensile_width")
        params["cable_count"] = st.number_input("Cable Count", 2, 12, params.get("cable_count", 4), 1, disabled=locked, key="dim_cable_count")
        
    elif typology == "portal_frame":
        params["eave_height"] = st.number_input("Eave Height (m)", 3.0, 15.0, params.get("eave_height", 6.0), 0.5, disabled=locked, key="dim_eave_height")
        params["span_width"] = st.number_input("Span Width (m)", 10.0, 50.0, params.get("span_width", 20.0), 0.5, disabled=locked, key="dim_portal_width")
        params["bay_spacing"] = st.number_input("Bay Spacing (m)", 4.0, 12.0, params.get("bay_spacing", 6.0), 0.5, disabled=locked, key="dim_bay_spacing")
        params["roof_pitch"] = st.number_input("Roof Pitch (°)", 1.0, 15.0, params.get("roof_pitch", 5.0), 0.5, disabled=locked, key="dim_roof_pitch")
        params["num_bays"] = st.number_input("Number of Bays", 2, 30, params.get("num_bays", 5), 1, disabled=locked, key="dim_portal_bays")
        
    elif typology == "arch_structure":
        params["span"] = st.number_input("Span (m)", 5.0, 50.0, params.get("span", 20.0), 0.5, disabled=locked, key="dim_arch_span")
        params["rise"] = st.number_input("Rise (m)", 2.0, 20.0, params.get("rise", 8.0), 0.5, disabled=locked, key="dim_arch_rise")
        
    elif typology == "cable_net":
        params["span"] = st.number_input("Span (m)", 5.0, 40.0, params.get("span", 20.0), 0.5, disabled=locked, key="dim_net_span")
        params["sag"] = st.number_input("Sag (m)", 1.0, 10.0, params.get("sag", 4.0), 0.5, disabled=locked, key="dim_net_sag")
        params["num_cables"] = st.number_input("Number of Cables", 3, 12, params.get("num_cables", 6), 1, disabled=locked, key="dim_net_cables")
        
    elif typology == "geodesic_dome":
        materials["dome_radius"] = st.number_input("Sphere Radius (m)", 5.0, 100.0, materials.get("dome_radius", 20.0), 1.0, disabled=locked, key="dome_radius")
        materials["dome_height"] = st.number_input("Dome Height (m)", 2.0, materials.get("dome_radius", 20) * 1.5, materials.get("dome_height", materials.get("dome_radius", 20)), 1.0, disabled=locked, key="dome_height")
        materials["dome_frequency"] = st.slider("Frequency (V)", 2, 12, materials.get("dome_frequency", 6), 1, disabled=locked, key="dome_frequency")
        estimated_members = 4 * materials["dome_frequency"]**2 + 2
        st.caption(f"📊 Estimated members: ~{estimated_members}")
        
    elif typology == "space_frame":
        params["span"] = st.number_input("Span (m)", 5.0, 80.0, params.get("span", 30.0), 0.5, disabled=locked, key="dim_sf_span")
        params["depth"] = st.number_input("Depth (m)", 0.5, 10.0, params.get("depth", 3.0), 0.5, disabled=locked, key="dim_sf_depth")
        params["grid_size"] = st.number_input("Grid Size (m)", 1.0, 8.0, params.get("grid_size", 3.0), 0.5, disabled=locked, key="dim_sf_grid")
        
    elif typology == "cable_stayed":
        params["span"] = st.number_input("Main Span (m)", 10.0, 200.0, params.get("span", 60.0), 2.0, disabled=locked, key="dim_cs_span")
        params["tower_height"] = st.number_input("Tower Height (m)", 5.0, 50.0, params.get("tower_height", 20.0), 1.0, disabled=locked, key="dim_cs_tower")
        params["cable_pairs"] = st.number_input("Cable Pairs per Side", 2, 12, params.get("cable_pairs", 6), 1, disabled=locked, key="dim_cs_cables")
        
    elif typology == "suspension_bridge":
        params["span"] = st.number_input("Main Span (m)", 20.0, 500.0, params.get("span", 150.0), 5.0, disabled=locked, key="dim_sb_span")
        params["tower_height"] = st.number_input("Tower Height (m)", 10.0, 80.0, params.get("tower_height", 40.0), 2.0, disabled=locked, key="dim_sb_tower")
        params["sag_ratio"] = st.slider("Sag Ratio (%)", 5, 15, params.get("sag_ratio", 10), 1, disabled=locked, key="dim_sb_sag")
        
    elif typology == "tensegrity":
        params["span"] = st.number_input("Diameter (m)", 5.0, 60.0, params.get("span", 20.0), 1.0, disabled=locked, key="dim_tg_span")
        params["height"] = st.number_input("Height (m)", 2.0, 25.0, params.get("height", 8.0), 0.5, disabled=locked, key="dim_tg_height")
        params["struts"] = st.number_input("Number of Struts", 6, 24, params.get("struts", 12), 2, disabled=locked, key="dim_tg_struts")
        
    elif typology == "grid_shell":
        params["span"] = st.number_input("Span (m)", 10.0, 100.0, params.get("span", 40.0), 2.0, disabled=locked, key="dim_gs_span")
        params["rise"] = st.number_input("Rise (m)", 2.0, 30.0, params.get("rise", 12.0), 1.0, disabled=locked, key="dim_gs_rise")
        params["grid_spacing"] = st.number_input("Grid Spacing (m)", 0.5, 5.0, params.get("grid_spacing", 2.0), 0.5, disabled=locked, key="dim_gs_grid")
        
    elif typology == "retractable_roof":
        params["span"] = st.number_input("Span (m)", 10.0, 80.0, params.get("span", 40.0), 2.0, disabled=locked, key="dim_rr_span")
        params["length"] = st.number_input("Length (m)", 10.0, 100.0, params.get("length", 50.0), 2.0, disabled=locked, key="dim_rr_length")
        params["segments"] = st.number_input("Number of Segments", 2, 10, params.get("segments", 4), 1, disabled=locked, key="dim_rr_segments")
        
    elif typology == "truss_system":
        params["span"] = st.number_input("Span (m)", 5.0, 80.0, params.get("span", 30.0), 1.0, disabled=locked, key="dim_ts_span")
        params["depth"] = st.number_input("Truss Depth (m)", 0.5, 8.0, params.get("depth", 3.0), 0.5, disabled=locked, key="dim_ts_depth")
        params["panels"] = st.number_input("Number of Panels", 4, 20, params.get("panels", 8), 1, disabled=locked, key="dim_ts_panels")
        
    elif typology == "frame_system":
        params["span"] = st.number_input("Span (m)", 5.0, 60.0, params.get("span", 25.0), 1.0, disabled=locked, key="dim_fs_span")
        params["height"] = st.number_input("Height (m)", 3.0, 20.0, params.get("height", 8.0), 0.5, disabled=locked, key="dim_fs_height")
        params["bays"] = st.number_input("Number of Bays", 2, 20, params.get("bays", 6), 1, disabled=locked, key="dim_fs_bays")
        
    elif typology == "mast_supported":
        params["mast_height"] = st.number_input("Mast Height (m)", 5.0, 60.0, params.get("mast_height", 20.0), 1.0, disabled=locked, key="dim_ms_mast")
        params["span"] = st.number_input("Span (m)", 5.0, 80.0, params.get("span", 30.0), 1.0, disabled=locked, key="dim_ms_span")
        params["cables"] = st.number_input("Number of Guy Cables", 3, 8, params.get("cables", 4), 1, disabled=locked, key="dim_ms_cables")
        
    elif typology == "shell_structure":
        params["span"] = st.number_input("Span (m)", 5.0, 80.0, params.get("span", 30.0), 1.0, disabled=locked, key="dim_sh_span")
        params["rise"] = st.number_input("Rise (m)", 1.0, 30.0, params.get("rise", 10.0), 0.5, disabled=locked, key="dim_sh_rise")
        params["thickness"] = st.number_input("Shell Thickness (mm)", 20, 300, params.get("thickness", 80), 10, disabled=locked, key="dim_sh_thickness")
        
    elif typology == "hybrid_system":
        params["span"] = st.number_input("Span (m)", 10.0, 100.0, params.get("span", 40.0), 2.0, disabled=locked, key="dim_hy_span")
        params["height"] = st.number_input("Height (m)", 3.0, 30.0, params.get("height", 12.0), 1.0, disabled=locked, key="dim_hy_height")
        st.selectbox("Primary System", ["Tensile + Frame", "Frame + Truss", "Cable + Frame"], key="dim_hy_type")
        
    elif typology == "folded_plate":
        params["span"] = st.number_input("Span (m)", 5.0, 50.0, params.get("span", 20.0), 1.0, disabled=locked, key="dim_fp_span")
        params["width"] = st.number_input("Width (m)", 3.0, 30.0, params.get("width", 12.0), 0.5, disabled=locked, key="dim_fp_width")
        params["folds"] = st.number_input("Number of Folds", 3, 12, params.get("folds", 6), 1, disabled=locked, key="dim_fp_folds")
        
    elif typology == "stress_ribbon":
        params["span"] = st.number_input("Span (m)", 10.0, 100.0, params.get("span", 40.0), 2.0, disabled=locked, key="dim_sr_span")
        params["sag"] = st.number_input("Sag (m)", 0.5, 5.0, params.get("sag", 2.0), 0.1, disabled=locked, key="dim_sr_sag")
        params["width"] = st.number_input("Ribbon Width (m)", 1.0, 6.0, params.get("width", 3.0), 0.5, disabled=locked, key="dim_sr_width")
        
    elif typology == "inflatable_structure":
        params["span"] = st.number_input("Span (m)", 5.0, 50.0, params.get("span", 20.0), 1.0, disabled=locked, key="dim_in_span")
        params["height"] = st.number_input("Height (m)", 2.0, 20.0, params.get("height", 8.0), 0.5, disabled=locked, key="dim_in_height")
        params["pressure"] = st.slider("Internal Pressure (kPa)", 0.5, 5.0, params.get("pressure", 2.0), 0.1, disabled=locked, key="dim_in_pressure")
        
    elif typology == "fabricated_beam":
        params["span"] = st.number_input("Span (m)", 5.0, 40.0, params.get("span", 15.0), 0.5, disabled=locked, key="dim_fb_span")
        params["depth"] = st.number_input("Beam Depth (mm)", 100, 1000, params.get("depth", 400), 50, disabled=locked, key="dim_fb_depth")
        params["width"] = st.number_input("Beam Width (mm)", 50, 500, params.get("width", 200), 10, disabled=locked, key="dim_fb_width")
        
    elif typology == "roof_system":
        params["span"] = st.number_input("Span (m)", 5.0, 80.0, params.get("span", 30.0), 1.0, disabled=locked, key="dim_rs_span")
        params["length"] = st.number_input("Length (m)", 5.0, 100.0, params.get("length", 40.0), 1.0, disabled=locked, key="dim_rs_length")
        params["pitch"] = st.slider("Roof Pitch (°)", 0, 30, params.get("pitch", 10), 1, disabled=locked, key="dim_rs_pitch")
        
    elif typology == "bridge_viaduct":
        params["span"] = st.number_input("Span (m)", 10.0, 200.0, params.get("span", 60.0), 2.0, disabled=locked, key="dim_bv_span")
        params["width"] = st.number_input("Width (m)", 5.0, 30.0, params.get("width", 12.0), 0.5, disabled=locked, key="dim_bv_width")
        params["girders"] = st.number_input("Number of Girders", 2, 8, params.get("girders", 4), 1, disabled=locked, key="dim_bv_girders")
        
    elif typology == "shade_structure":
        params["span"] = st.number_input("Span (m)", 3.0, 30.0, params.get("span", 12.0), 0.5, disabled=locked, key="dim_ss_span")
        params["width"] = st.number_input("Width (m)", 3.0, 20.0, params.get("width", 8.0), 0.5, disabled=locked, key="dim_ss_width")
        params["height"] = st.number_input("Height (m)", 2.0, 8.0, params.get("height", 4.0), 0.5, disabled=locked, key="dim_ss_height")
        
    else:
        st.info(f"Input form for {typology} coming soon")
        
    st.markdown('</div>', unsafe_allow_html=True)
    
    return params, materials

# ============================================================
# GEODESIC DOME MATH FUNCTIONS
# ============================================================
def generate_octahedron_dome(radius, frequency, height=None):
    octa_vertices = [
        (0, 0, 1), (1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0), (0, 0, -1)
    ]
    octa_faces = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),
        (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4)
    ]
    
    nodes = []
    members = []
    
    for face in octa_faces:
        p1 = octa_vertices[face[0]]
        p2 = octa_vertices[face[1]]
        p3 = octa_vertices[face[2]]
        subdivided = subdivide_triangle(p1, p2, p3, frequency, radius)
        nodes.extend(subdivided["nodes"])
        members.extend(subdivided["members"])
    
    nodes, members = deduplicate_geometry(nodes, members)
    
    if height is not None:
        nodes = [n for n in nodes if n[2] >= (radius - height)]
    
    return nodes, members

def subdivide_triangle(p1, p2, p3, freq, radius):
    nodes = []
    members = []
    
    for i in range(freq + 1):
        for j in range(freq + 1 - i):
            a = i / freq
            b = j / freq
            c = 1 - a - b
            
            x = a * p1[0] + b * p2[0] + c * p3[0]
            y = a * p1[1] + b * p2[1] + c * p3[1]
            z = a * p1[2] + b * p2[2] + c * p3[2]
            
            norm = math.sqrt(x*x + y*y + z*z)
            if norm > 0:
                x = x / norm * radius
                y = y / norm * radius
                z = z / norm * radius
            
            nodes.append((x, y, z))
    
    for i in range(freq):
        for j in range(freq - i):
            idx = i * (freq + 1) + j
            members.append((idx, idx + 1))
            members.append((idx, idx + freq + 1))
            if j < freq - i:
                members.append((idx, idx + freq + 2))
    
    return {"nodes": nodes, "members": members}

def deduplicate_geometry(nodes, members):
    tolerance = 0.001
    unique_nodes = []
    node_map = {}
    
    for i, node in enumerate(nodes):
        found = False
        for j, unique in enumerate(unique_nodes):
            if (abs(node[0] - unique[0]) < tolerance and
                abs(node[1] - unique[1]) < tolerance and
                abs(node[2] - unique[2]) < tolerance):
                node_map[i] = j
                found = True
                break
        if not found:
            node_map[i] = len(unique_nodes)
            unique_nodes.append(node)
    
    unique_members = []
    for m in members:
        n1 = node_map.get(m[0], m[0])
        n2 = node_map.get(m[1], m[1])
        if n1 != n2:
            unique_members.append((n1, n2))
    
    return unique_nodes, unique_members

def calculate_member_lengths(nodes, members):
    lengths = []
    for m in members:
        p1 = nodes[m[0]]
        p2 = nodes[m[1]]
        length = math.sqrt(
            (p1[0] - p2[0])**2 +
            (p1[1] - p2[1])**2 +
            (p1[2] - p2[2])**2
        )
        lengths.append(length)
    return lengths

def group_members_by_length(lengths, tolerance=0.01):
    groups = []
    for length in lengths:
        found = False
        for group in groups:
            if abs(group["length"] - length) < tolerance:
                group["members"].append(length)
                group["count"] += 1
                found = True
                break
        if not found:
            groups.append({"length": length, "count": 1, "members": [length]})
    groups.sort(key=lambda x: x["length"])
    return groups

def calculate_length_std_dev(lengths):
    n = len(lengths)
    if n == 0:
        return 0
    mean = sum(lengths) / n
    variance = sum((L - mean)**2 for L in lengths) / n
    return math.sqrt(variance)

def estimate_member_forces(nodes, members, total_load):
    num_nodes = len(nodes)
    if num_nodes == 0:
        return []
    
    load_per_node = total_load / num_nodes
    forces = []
    
    for m in members:
        p1 = nodes[m[0]]
        p2 = nodes[m[1]]
        length = math.sqrt(
            (p2[0] - p1[0])**2 +
            (p2[1] - p1[1])**2 +
            (p2[2] - p1[2])**2
        )
        dz = abs(p2[2] - p1[2])
        vertical_ratio = dz / length if length > 0 else 0.5
        angle_factor = 0.5 + 0.5 * vertical_ratio
        force = load_per_node * length * angle_factor * 0.5
        forces.append(force)
    
    return forces

def calculate_buckling_pressure(radius, thickness, E=210000, nu=0.3):
    if radius <= 0 or thickness <= 0:
        return 0
    ratio = thickness / radius
    p_cr = 0.3 * E * ratio**2 / math.sqrt(1 - nu**2)
    return p_cr

def check_buckling(radius, thickness, applied_load, safety_factor=1.5):
    if radius <= 0:
        return {"critical_pressure": 0, "applied_pressure": 0, "safety_factor": 0, "is_safe": False, "status": "❌ ERROR"}
    
    p_cr = calculate_buckling_pressure(radius, thickness)
    pressure = applied_load / (math.pi * radius**2) if radius > 0 else 0
    safety = p_cr / pressure if pressure > 0 else 100
    is_safe = safety >= safety_factor
    
    return {
        "critical_pressure": p_cr,
        "applied_pressure": pressure,
        "safety_factor": safety,
        "is_safe": is_safe,
        "status": "✅ PASS" if is_safe else "⚠️ CHECK"
    }

def design_geodesic_dome(params):
    radius = params.get("radius", 20)
    frequency = params.get("frequency", 6)
    height = params.get("height", radius)
    total_load = params.get("total_load", 500)
    thickness = params.get("thickness", 0.050)
    
    nodes, members = generate_octahedron_dome(radius, frequency, height)
    
    if len(nodes) == 0:
        return {
            "nodes": [],
            "members": [],
            "num_nodes": 0,
            "num_members": 0,
            "error": "No nodes generated. Check parameters."
        }
    
    lengths = calculate_member_lengths(nodes, members)
    groups = group_members_by_length(lengths)
    forces = estimate_member_forces(nodes, members, total_load)
    buckling = check_buckling(radius, thickness, total_load)
    length_std = calculate_length_std_dev(lengths)
    
    score = 100
    if not buckling["is_safe"]:
        score -= 25
    if length_std > 0.5:
        score -= 10
    if len(groups) > 3:
        score -= 5
    
    health_score = max(0, min(100, score))
    
    return {
        "nodes": nodes,
        "members": members,
        "num_nodes": len(nodes),
        "num_members": len(members),
        "member_groups": groups,
        "member_forces": forces,
        "total_length": sum(lengths) if lengths else 0,
        "avg_length": sum(lengths) / len(lengths) if lengths else 0,
        "length_std_dev": length_std,
        "buckling_check": buckling,
        "health_score": health_score
    }

# ============================================================
# 3D GENERATORS - ENHANCED
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

    if materials:
        num_bays = materials.get("num_bays", 2)
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 30)
        
        bracing_x = generate_bracing_positions(span, num_bays)
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
                x=[x1, anchor_x],
                y=[y2_pt, anchor2_y],
                z=[z_pt, 0],
                mode='lines',
                line=dict(color='#FFD93D', width=3),
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
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

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
    fig.update_layout(scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)', bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_arch(params):
    span, rise = params.get("span", 20.0), params.get("rise", 8.0)
    num_points = 50
    x = np.linspace(-span/2, span/2, num_points)
    z = rise * (1 - (2*x/span)**2)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', name='Arch', line=dict(width=6, color='#FF6B6B')))
    fig.add_trace(go.Scatter3d(x=[-span/2, span/2], y=[0,0], z=[0,0], mode='markers', name='Supports', marker=dict(color='#4ECDC4', size=10, symbol='square')))
    fig.update_layout(scene=dict(xaxis_title='Span (m)', yaxis_title='Width (m)', zaxis_title='Height (m)', bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_cable_net(params):
    span, sag, cables = params.get("span", 20.0), params.get("sag", 4.0), params.get("num_cables", 6)
    num_points = 30
    x = np.linspace(-span/2, span/2, num_points)
    z = sag * (1 - (2*x/span)**2)
    
    fig = go.Figure()
    for i in range(cables):
        y = i * span/(cables-1) - span/2
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(color='#4a7a9c', width=2), showlegend=False))
    
    for i in range(cables):
        y = i * span/(cables-1) - span/2
        fig.add_trace(go.Scatter3d(x=[x[i], x[-i-1]], y=[y, y], z=[z[i], z[-i-1]], mode='lines', line=dict(color='#f39c12', width=1.5), showlegend=False))
    
    fig.update_layout(scene=dict(xaxis_title='Span (m)', yaxis_title='Width (m)', zaxis_title='Height (m)', bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_geodesic_dome_3d(params):
    radius = params.get("radius", 20)
    frequency = params.get("frequency", 6)
    height = params.get("height", radius)
    
    nodes, members = generate_octahedron_dome(radius, frequency, height)
    
    fig = go.Figure()
    
    for m in members:
        if m[0] < len(nodes) and m[1] < len(nodes):
            p1 = nodes[m[0]]
            p2 = nodes[m[1]]
            fig.add_trace(go.Scatter3d(
                x=[p1[0], p2[0]],
                y=[p1[1], p2[1]],
                z=[p1[2], p2[2]],
                mode='lines',
                line=dict(color='#4a7a9c', width=2),
                showlegend=False
            ))
    
    if nodes:
        xs = [n[0] for n in nodes]
        ys = [n[1] for n in nodes]
        zs = [n[2] for n in nodes]
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='markers',
            marker=dict(color='#f39c12', size=4),
            name='Nodes'
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

# ============================================================
# SIMPLE 3D GENERATORS FOR OTHER STRUCTURES (Feature 1)
# ============================================================
def generate_simple_structure_3d(params, typology):
    """Generate simple 3D visualization for any structure type"""
    fig = go.Figure()
    
    span = params.get("span", params.get("B", 20))
    height = params.get("height", params.get("rise", params.get("A", 8)))
    width = params.get("width", 10)
    
    # Create a simple wireframe for any structure
    num_points = 20
    x = np.linspace(-span/2, span/2, num_points)
    
    if typology in ["saddle_span", "arch_structure", "shell_structure"]:
        z = height * (1 - (2*x/span)**2)
        fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', line=dict(color='#4a7a9c', width=4), name='Main Curve'))
    
    elif typology in ["portal_frame", "frame_system"]:
        # Simple portal frame
        x_frame = [-span/2, -span/2, span/2, span/2]
        z_frame = [0, height, height, 0]
        fig.add_trace(go.Scatter3d(x=x_frame, y=[0]*len(x_frame), z=z_frame, mode='lines', line=dict(color='#4a7a9c', width=4), name='Portal Frame'))
        fig.add_trace(go.Scatter3d(x=x_frame, y=[width]*len(x_frame), z=z_frame, mode='lines', line=dict(color='#4a7a9c', width=4), showlegend=False))
        # Roof
        fig.add_trace(go.Scatter3d(x=[-span/2, span/2], y=[0, 0], z=[height, height], mode='lines', line=dict(color='#f39c12', width=3), showlegend=False))
        fig.add_trace(go.Scatter3d(x=[-span/2, span/2], y=[width, width], z=[height, height], mode='lines', line=dict(color='#f39c12', width=3), showlegend=False))
    
    elif typology in ["tensile_membrane", "clear_span_tent"]:
        # Tent shape
        x = np.linspace(-span/2, span/2, 20)
        y = np.linspace(-width/2, width/2, 20)
        X, Y = np.meshgrid(x, y)
        Z = height * (1 - (2*X/span)**2) * (1 - (2*Y/width)**2)
        fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.5, colorscale='Viridis', showscale=False, name='Membrane'))
    
    elif typology == "geodesic_dome":
        # Use the actual dome generator
        return generate_geodesic_dome_3d(params)
    
    else:
        # Generic structure visualization
        x = np.linspace(-span/2, span/2, 20)
        z = height * (1 - (2*x/span)**2)
        fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', line=dict(color='#4a7a9c', width=4), name='Structure'))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Span (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)',
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

# ============================================================
# GENERATORS DICTIONARY
# ============================================================
GENERATORS = {
    "saddle_span": generate_saddle_span,
    "clear_span_tent": generate_tent,
    "tensile_membrane": generate_tensile,
    "portal_frame": generate_portal,
    "arch_structure": generate_arch,
    "cable_net": generate_cable_net,
    "geodesic_dome": generate_geodesic_dome_3d,
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

def calculate_required_section(load_kN, span_m, material_type, section_type, fy=355, typology="saddle_span", rise_m=6.0):
    safety = 1.5
    w = load_kN / span_m
    M_beam = (w * span_m**2) / 8
    
    if typology == "saddle_span":
        arch_reduction = max(0.35, 1 - (rise_m / span_m) * 0.55)
        M = M_beam * arch_reduction
    else:
        arch_reduction = 1.0
        M = M_beam
    
    M_Nmm = M * 1e6
    W_required = M_Nmm / (fy / safety)
    
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
    
    for section, props in sections_in_type:
        if props["W_el"] >= W_required * W_factor and props["I"] >= I_required * I_factor:
            selected_section = section
            selected_props = props
            selection_note = None
            break
    
    if not selected_section:
        for section, props in sections_in_type:
            if props["W_el"] >= W_required * W_factor:
                selected_section = section
                selected_props = props
                selection_note = "⚠️ Deflection may be slightly higher than ideal"
                break
    
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

# ============================================================
# TRUSS ANALYSIS
# ============================================================
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
    type_map = {
        "CHS": "CHS",
        "SHS": "SHS",
        "RHS": "RHS",
        "I-Beam": "I-Beam",
        "Angle": "Angle",
        "Channel": "Channel"
    }
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
# BQ GENERATOR - ENHANCED
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

def generate_dome_bill_of_quantities(dome_results, materials):
    """Generate BQ for geodesic dome"""
    num_members = dome_results.get("num_members", 0)
    total_length = dome_results.get("total_length", 0)
    avg_length = dome_results.get("avg_length", 0)
    groups = dome_results.get("member_groups", [])
    
    material_cost = MATERIAL_COSTS.get(materials.get("material_type", "Steel"), 2.5)
    country = materials.get("country", "Malaysia")
    currency = get_currency(country)
    
    bq_items = []
    total_cost = 0
    
    if groups:
        for i, group in enumerate(groups):
            weight = group["length"] * 10
            cost = weight * material_cost * group["count"]
            bq_items.append({
                "item": f"Strut Group {i+1} (Length: {group['length']:.2f}m)",
                "qty": group["count"],
                "unit": "pcs",
                "length_m": group["length"],
                "total_length_m": group["length"] * group["count"],
                "weight_kg": weight * group["count"],
                "unit_price": material_cost,
                "total_price": cost
            })
            total_cost += cost
    
    num_joints = dome_results.get("num_nodes", 0)
    connection_cost = num_joints * 50
    bq_items.append({
        "item": f"Joints/Connections ({num_joints} pcs)",
        "qty": num_joints,
        "unit": "pcs",
        "length_m": "-",
        "total_length_m": "-",
        "weight_kg": 0,
        "unit_price": 50,
        "total_price": connection_cost
    })
    total_cost += connection_cost
    
    installation_cost = total_cost * 0.15
    bq_items.append({
        "item": "Installation & Labour",
        "qty": 1,
        "unit": "lump sum",
        "length_m": "-",
        "total_length_m": "-",
        "weight_kg": 0,
        "unit_price": installation_cost,
        "total_price": installation_cost
    })
    total_cost += installation_cost
    
    return {
        "items": bq_items,
        "total_cost": total_cost,
        "total_steel_weight": sum([item.get("weight_kg", 0) for item in bq_items if "weight_kg" in item]),
        "total_fabric_area": 0,
        "total_cable_length": 0,
        "joint_type": "bolted",
        "joint_description": "Dome connections",
        "currency": currency
    }

# ============================================================
# EXPORT FUNCTIONS (Feature 4)
# ============================================================
def export_to_dxf(nodes, members, filename="structure.dxf"):
    """Export structure to DXF format"""
    import io
    
    dxf_content = []
    dxf_content.append("0")
    dxf_content.append("SECTION")
    dxf_content.append("2")
    dxf_content.append("ENTITIES")
    
    # Add members as lines
    for m in members:
        if m[0] < len(nodes) and m[1] < len(nodes):
            p1 = nodes[m[0]]
            p2 = nodes[m[1]]
            dxf_content.extend([
                "0", "LINE",
                "8", "0",
                "10", f"{p1[0]:.3f}",
                "20", f"{p1[1]:.3f}",
                "30", f"{p1[2]:.3f}",
                "11", f"{p2[0]:.3f}",
                "21", f"{p2[1]:.3f}",
                "31", f"{p2[2]:.3f}"
            ])
    
    # Add nodes as points
    for node in nodes:
        dxf_content.extend([
            "0", "POINT",
            "8", "1",
            "10", f"{node[0]:.3f}",
            "20", f"{node[1]:.3f}",
            "30", f"{node[2]:.3f}"
        ])
    
    dxf_content.extend(["0", "ENDSEC", "0", "EOF"])
    
    return "\n".join(dxf_content)

def export_to_csv(results, filename="structure.csv"):
    """Export results to CSV"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Parameter", "Value"])
    
    # Write loads
    loads = results.get("loads", {})
    for key, value in loads.items():
        writer.writerow([f"Load_{key}", f"{value:.2f} kN"])
    
    # Write beam data
    beam = results.get("beams", {}).get("main", {})
    if beam:
        writer.writerow(["Selected_Section", beam.get("section", "N/A")])
        writer.writerow(["Moment_Capacity", f"{beam.get('moment_capacity', 0):.2f} kNm"])
        writer.writerow(["Required_Moment", f"{beam.get('required_moment', 0):.2f} kNm"])
        writer.writerow(["Adequate", beam.get("is_adequate", False)])
    
    # Write health score
    writer.writerow(["Health_Score", results.get("health_score", 0)])
    
    return output.getvalue()

def export_to_json(results, filename="structure.json"):
    """Export results to JSON"""
    # Convert numpy types to Python types
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

def export_to_pdf(results, project_info, materials, filename="report.pdf"):
    """Export results to PDF using matplotlib"""
    try:
        fig, axes = plt.subplots(2, 2, figsize=(10, 12))
        fig.patch.set_facecolor('#0a0e17')
        
        axes[0, 0].axis('off')
        axes[0, 0].text(0.5, 0.8, "SDSe - Intelligent Fluid Design Workplace", fontsize=18, color='white', ha='center', weight='bold')
        axes[0, 0].text(0.5, 0.6, f"Project: {project_info.get('name', 'Untitled')}", fontsize=14, color='#b0c4de', ha='center')
        axes[0, 0].text(0.5, 0.4, f"Client: {project_info.get('client', 'Unknown')}", fontsize=12, color='#b0c4de', ha='center')
        axes[0, 0].text(0.5, 0.2, f"Date: {datetime.now().strftime('%B %d, %Y')}", fontsize=12, color='#b0c4de', ha='center')
        
        axes[0, 1].axis('off')
        axes[0, 1].text(0.1, 0.9, "Design Summary", fontsize=14, color='white', weight='bold')
        
        loads = results.get('loads', {})
        y_pos = 0.8
        for key, value in loads.items():
            axes[0, 1].text(0.1, y_pos, f"{key.title()}: {value:.1f} kN", fontsize=11, color='#b0c4de')
            y_pos -= 0.08
        
        fabric = results.get('fabric', {})
        cables = results.get('cables', {})
        axes[0, 1].text(0.1, y_pos - 0.05, f"Fabric: {fabric.get('type', 'N/A')} ({fabric.get('thickness', 'N/A')}mm)", fontsize=11, color='#b0c4de')
        y_pos -= 0.08
        axes[0, 1].text(0.1, y_pos, f"Cable: {cables.get('type', 'N/A')} {cables.get('diameter', 'N/A')}mm", fontsize=11, color='#b0c4de')
        
        axes[1, 0].axis('off')
        score = results.get('health_score', 0)
        color = '#2ecc71' if score >= 80 else '#f39c12' if score >= 60 else '#e74c3c'
        axes[1, 0].text(0.5, 0.6, "Health Score", fontsize=14, color='white', ha='center', weight='bold')
        axes[1, 0].text(0.5, 0.3, f"{score}%", fontsize=36, color=color, ha='center', weight='bold')
        
        bq = results.get('bq', {})
        axes[1, 1].axis('off')
        axes[1, 1].text(0.1, 0.9, "Cost Summary", fontsize=14, color='white', weight='bold')
        axes[1, 1].text(0.1, 0.75, f"Total Cost: {format_currency(bq.get('total_cost', 0), materials.get('country', 'Malaysia'))}", fontsize=12, color='#b0c4de')
        axes[1, 1].text(0.1, 0.6, f"Steel Weight: {bq.get('total_steel_weight', 0):.0f} kg", fontsize=12, color='#b0c4de')
        axes[1, 1].text(0.1, 0.45, f"Joint Type: {bq.get('joint_type', 'bolted').upper()}", fontsize=12, color='#b0c4de')
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='pdf', facecolor='#0a0e17', edgecolor='none')
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None

# ============================================================
# MAIN DESIGN ENGINE
# ============================================================
def auto_design_structure(params, materials, typology="saddle_span"):
    """Main design engine - routes to appropriate calculation method"""
    
    # Special handling for geodesic dome
    if typology == "geodesic_dome":
        dome_params = {
            "radius": materials.get("dome_radius", 20),
            "frequency": materials.get("dome_frequency", 6),
            "height": materials.get("dome_height", 20),
            "total_load": 500,
            "thickness": 0.050
        }
        
        dome_results = design_geodesic_dome(dome_params)
        
        results = {
            "loads": {"total": 500, "wind": 0, "dead": 0, "live": 0},
            "beams": {},
            "truss": {},
            "fabric": {},
            "cables": {},
            "all_checks": {},
            "health_score": dome_results.get("health_score", 50),
            "joint_type": materials.get("joint_type", "bolted"),
            "country": materials.get("country", "Malaysia"),
            "typology": typology,
            "dome_data": dome_results
        }
        
        results["all_checks"]["num_nodes"] = {"status": f"📍 {dome_results.get('num_nodes', 0)}", "value": "Nodes"}
        results["all_checks"]["num_members"] = {"status": f"🔗 {dome_results.get('num_members', 0)}", "value": "Members"}
        results["all_checks"]["length_std"] = {"status": f"📊 {dome_results.get('length_std_dev', 0):.3f}", "value": "Std Dev"}
        results["all_checks"]["buckling"] = {"status": dome_results.get('buckling_check', {}).get('status', '⚠️ CHECK'), "value": f"SF: {dome_results.get('buckling_check', {}).get('safety_factor', 0):.2f}"}
        
        bq = generate_dome_bill_of_quantities(dome_results, materials)
        results["bq"] = bq
        
        return results
    
    # Original structure types
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
    <div style='display: flex; justify-content: flex-end; padding: 0.2rem 0;'>
        <span class='license-badge license-free'>
            SDSe - Free & Open
        </span>
        <span style='color: #8a9aaa; font-size: 0.7rem; margin-left: 1rem;'>
            Projects: {len(st.session_state.saved_projects)} / Unlimited
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

# ============================================================
# DASHBOARD PAGE
# ============================================================
def render_dashboard():
    st.title("🏗️ SDSe - Intelligent Fluid Design Workplace")
    st.caption("*Design. Analyze. Build. All Free.*")
    
    st.markdown("## 🚀 Start Your Design")
    st.markdown("Choose how you'd like to begin:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="design-path-card">
            <div class="icon">💡</div>
            <div class="title">Intelligent Fluid Design</div>
            <div class="desc">"I need help deciding"<br>
            Answer a few questions and we'll recommend<br>
            the best structure for your needs</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Intelligent Design", key="start_guided", use_container_width=True, type="primary"):
            st.session_state.page = "intelligent_design"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="design-path-card">
            <div class="icon">⚡</div>
            <div class="title">Direct Design</div>
            <div class="desc">"I know what I want"<br>
            Choose from 25 Structure Types and<br>
            go straight to design</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Direct Design", key="start_direct", use_container_width=True, type="primary"):
            st.session_state.page = "catalog"
            st.rerun()
    
    st.divider()
    
    projects = st.session_state.saved_projects
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>📂</div><div class='value'>{len(projects)}</div><div class='label'>Saved Projects</div></div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>🏗️</div><div class='value'>25</div><div class='label'>Structure Types</div></div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>🔧</div><div class='value'>100+</div><div class='label'>Sections Available</div></div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>⚡</div><div class='value'>AI</div><div class='label'>Intelligent Engine</div></div>", unsafe_allow_html=True)
    
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
# INTELLIGENT DESIGN PAGE
# ============================================================
def render_intelligent_design():
    st.title("💡 Intelligent Fluid Design")
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
            # Recommendation logic
            if span_range == "> 60m" or budget == "High":
                recommended = "cable_stayed"
            elif span_range == "< 20m" or budget == "Low":
                recommended = "portal_frame"
            elif function in ["Architectural Feature", "Event Space"]:
                recommended = "tensile_membrane"
            elif permanence == "Temporary":
                recommended = "clear_span_tent"
            elif aesthetics == "Dramatic/Ironic":
                recommended = "geodesic_dome"
            else:
                recommended = "saddle_span"
            
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

# ============================================================
# REGISTRATION PAGE
# ============================================================
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
# CATALOG PAGE - 25 STRUCTURE TYPES (Feature 1)
# ============================================================
def render_catalog():
    st.subheader("🏗️ Choose a Structure Type")
    st.caption("Select from 25 different structure types")
    
    # Category tabs
    categories = ["All", "Tensile", "Frame", "Spatial", "Specialized"]
    selected_category = st.radio("Filter by Category", categories, horizontal=True)
    
    items = list(STRUCTURE_TYPES.items())
    
    # Filter by category
    if selected_category != "All":
        items = [(k, v) for k, v in items if v.get("category") == selected_category]
    
    # Display in grid (3 columns)
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(items):
                key, data = items[i + j]
                with cols[j]:
                    st.markdown(f"""
                    <div class="design-path-card">
                        <div class="icon">{data['icon']}</div>
                        <div class="title">{data['name']}</div>
                        <div class="desc">{data['description']}</div>
                        <div style="margin-top: 0.5rem; font-size: 0.7rem; color: #6a7a8a;">{data.get('category', 'General')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Select {data['name']}", key=f"catalog_{key}", use_container_width=True, type="primary"):
                        st.session_state.typology = key
                        
                        # Set default params based on structure type
                        if key == "geodesic_dome":
                            st.session_state.params = {}
                            st.session_state.materials["dome_radius"] = 20
                            st.session_state.materials["dome_frequency"] = 6
                            st.session_state.materials["dome_height"] = 20
                        elif key in ["saddle_span", "tensile_membrane"]:
                            st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
                        elif key == "clear_span_tent":
                            st.session_state.params = {"span_width": 10.0, "ridge_height": 5.0, "bay_distance": 5.0, "num_bays": 4}
                        elif key == "portal_frame":
                            st.session_state.params = {"eave_height": 6.0, "span_width": 20.0, "bay_spacing": 6.0, "roof_pitch": 5.0, "num_bays": 5}
                        elif key == "arch_structure":
                            st.session_state.params = {"span": 20.0, "rise": 8.0}
                        elif key == "cable_net":
                            st.session_state.params = {"span": 20.0, "sag": 4.0, "num_cables": 6}
                        elif key == "space_frame":
                            st.session_state.params = {"span": 30.0, "depth": 3.0, "grid_size": 3.0}
                        elif key == "cable_stayed":
                            st.session_state.params = {"span": 60.0, "tower_height": 20.0, "cable_pairs": 6}
                        elif key == "suspension_bridge":
                            st.session_state.params = {"span": 150.0, "tower_height": 40.0, "sag_ratio": 10}
                        else:
                            st.session_state.params = {"B": 10.0, "A": 6.0, "LAA": 15.0}
                        
                        st.session_state.page = "workspace"
                        st.rerun()

# ============================================================
# BQ & COSTING PAGE - ENHANCED WITH EXPORT (Feature 4)
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
    
    # Export Section (Feature 4)
    st.subheader("📤 Export Options")
    st.caption("Download BQ in multiple formats")
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        if st.button("📥 Download CSV", key="bq_download_csv", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"BQ_{st.session_state.project_info.get('reference', 'project')}.csv",
                mime="text/csv",
                key="bq_download_btn"
            )
    
    with export_col2:
        if st.button("📊 Download Excel", key="bq_download_excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='BQ', index=False)
                # Add summary sheet
                summary_data = {
                    'Metric': ['Total Cost', 'Steel Weight', 'Fabric Area', 'Joint Type'],
                    'Value': [
                        f"{currency['symbol']}{bq['total_cost']:,.0f}",
                        f"{bq['total_steel_weight']:.0f} kg",
                        f"{bq['total_fabric_area']:.0f} m²",
                        bq.get('joint_type', 'bolted').upper()
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            output.seek(0)
            
            st.download_button(
                label="📊 Download Excel",
                data=output,
                file_name=f"BQ_{st.session_state.project_info.get('reference', 'project')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="bq_download_excel_btn"
            )
    
    with export_col3:
        if st.button("📄 Download JSON", key="bq_download_json", use_container_width=True):
            json_data = json.dumps(bq, indent=2, default=str)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"BQ_{st.session_state.project_info.get('reference', 'project')}.json",
                mime="application/json",
                key="bq_download_json_btn"
            )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to Workspace", key="bq_back_workspace", use_container_width=True, type="secondary"):
            st.session_state.page = "workspace"
            st.rerun()
    with col2:
        if st.button("📊 Reports", key="bq_to_reports", use_container_width=True, type="primary"):
            st.session_state.page = "reports"
            st.rerun()

# ============================================================
# REPORTS PAGE - ENHANCED WITH ALL EXPORTS (Feature 4 & 5)
# ============================================================
def render_reports():
    st.title("📊 Reports & Export")
    st.caption("Generate professional reports and export in multiple formats")
    
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
    
    # Report Options
    report_type = st.radio(
        "Select Report Type",
        ["📄 Summary Report", "📋 Detailed Report", "📊 Cost Report", "🔧 Technical Report"],
        horizontal=True
    )
    
    st.divider()
    
    # Export buttons row
    st.subheader("📤 Export Options")
    export_cols = st.columns(5)
    
    # PDF Export
    with export_cols[0]:
        if st.button("📄 PDF", key="export_pdf", use_container_width=True, type="primary"):
            pdf_buf = export_to_pdf(
                design_results,
                st.session_state.project_info,
                st.session_state.materials
            )
            if pdf_buf:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_buf,
                    file_name=f"SDSe_Report_{st.session_state.project_info.get('reference', 'project')}.pdf",
                    mime="application/pdf",
                    key="pdf_download_btn"
                )
                st.success("✅ PDF ready!")
    
    # DXF Export
    with export_cols[1]:
        if st.button("📐 DXF", key="export_dxf", use_container_width=True):
            dome_data = design_results.get("dome_data", {})
            nodes = dome_data.get("nodes", [])
            members = dome_data.get("members", [])
            
            if nodes and members:
                dxf_content = export_to_dxf(nodes, members)
                st.download_button(
                    label="📥 Download DXF",
                    data=dxf_content,
                    file_name=f"Structure_{st.session_state.project_info.get('reference', 'project')}.dxf",
                    mime="application/dxf",
                    key="dxf_download_btn"
                )
                st.success("✅ DXF ready!")
            else:
                st.warning("⚠️ 3D data not available for this structure type")
    
    # CSV Export
    with export_cols[2]:
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
    
    # JSON Export
    with export_cols[3]:
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
    
    # All-in-One ZIP Export (Feature 5)
    with export_cols[4]:
        if st.button("📦 ZIP All", key="export_zip", use_container_width=True, type="secondary"):
            try:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add PDF
                    pdf_buf = export_to_pdf(
                        design_results,
                        st.session_state.project_info,
                        st.session_state.materials
                    )
                    if pdf_buf:
                        zip_file.writestr(f"Report_{st.session_state.project_info.get('reference', 'project')}.pdf", pdf_buf.getvalue())
                    
                    # Add CSV
                    csv_data = export_to_csv(design_results)
                    zip_file.writestr(f"Results_{st.session_state.project_info.get('reference', 'project')}.csv", csv_data)
                    
                    # Add JSON
                    json_data = export_to_json(design_results)
                    zip_file.writestr(f"Results_{st.session_state.project_info.get('reference', 'project')}.json", json_data)
                    
                    # Add BQ if available
                    bq = design_results.get("bq", {})
                    if bq and "items" in bq:
                        bq_data = []
                        for item in bq["items"]:
                            bq_data.append({
                                "Item": item["item"],
                                "Qty": item["qty"],
                                "Unit": item["unit"],
                                "Length (m)": item["length_m"],
                                "Total Length (m)": item["total_length_m"],
                                "Weight (kg)": item["weight_kg"],
                                "Unit Price": item["unit_price"],
                                "Total": item["total_price"]
                            })
                        df = pd.DataFrame(bq_data)
                        csv_bq = df.to_csv(index=False)
                        zip_file.writestr(f"BQ_{st.session_state.project_info.get('reference', 'project')}.csv", csv_bq)
                    
                    # Add DXF if available
                    dome_data = design_results.get("dome_data", {})
                    nodes = dome_data.get("nodes", [])
                    members = dome_data.get("members", [])
                    if nodes and members:
                        dxf_content = export_to_dxf(nodes, members)
                        zip_file.writestr(f"Structure_{st.session_state.project_info.get('reference', 'project')}.dxf", dxf_content)
                
                zip_buffer.seek(0)
                st.download_button(
                    label="📥 Download ZIP",
                    data=zip_buffer,
                    file_name=f"SDSe_Complete_{st.session_state.project_info.get('reference', 'project')}.zip",
                    mime="application/zip",
                    key="zip_download_btn"
                )
                st.success("✅ ZIP package ready! Includes PDF, CSV, JSON, BQ, and DXF")
            except Exception as e:
                st.error(f"ZIP generation error: {str(e)}")
    
    st.divider()
    
    # Report Preview
    st.subheader("📋 Report Preview")
    
    if report_type == "📄 Summary Report":
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Project Summary")
        st.markdown(f"**Project:** {st.session_state.project_info.get('name', 'Untitled')}")
        st.markdown(f"**Client:** {st.session_state.project_info.get('client', 'Unknown')}")
        st.markdown(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")
        st.markdown(f"**Reference:** {st.session_state.project_info.get('reference', 'N/A')}")
        st.markdown("---")
        st.markdown("### 📊 Design Results")
        loads = design_results.get("loads", {})
        for key, value in loads.items():
            st.metric(key.title(), f"{value:.1f} kN")
        st.markdown("---")
        score = design_results.get("health_score", 0)
        color = "#2ecc71" if score >= 80 else "#f39c12" if score >= 60 else "#e74c3c"
        st.markdown(f"### 🏥 Health Score: **<span style='color:{color};font-size:2rem;'>{score}%</span>**", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    elif report_type == "📋 Detailed Report":
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Detailed Design Report")
        
        # Loads
        st.markdown("#### 📊 Loads")
        loads = design_results.get("loads", {})
        for key, value in loads.items():
            st.metric(key.title(), f"{value:.1f} kN")
        
        # Beams
        beam = design_results.get("beams", {}).get("main", {})
        if beam:
            st.markdown("#### 🔧 Member Selection")
            st.markdown(f"**Section:** {beam.get('section', 'N/A')}")
            st.markdown(f"**Moment Capacity:** {beam.get('moment_capacity', 0):.1f} kNm")
            st.markdown(f"**Required Moment:** {beam.get('required_moment', 0):.1f} kNm")
            st.markdown(f"**Adequate:** {'✅ Yes' if beam.get('is_adequate', False) else '⚠️ Check'}")
        
        # Fabric
        fabric = design_results.get("fabric", {})
        if fabric:
            st.markdown("#### 🧵 Fabric")
            st.markdown(f"**Type:** {fabric.get('type', 'N/A')}")
            st.markdown(f"**Thickness:** {fabric.get('thickness', 'N/A')} mm")
            st.markdown(f"**Strength:** {fabric.get('strength', 0):.0f} kN/m")
        
        # Cables
        cables = design_results.get("cables", {})
        if cables:
            st.markdown("#### 🔗 Cables")
            st.markdown(f"**Type:** {cables.get('type', 'N/A')}")
            st.markdown(f"**Diameter:** {cables.get('diameter', 'N/A')} mm")
            st.markdown(f"**Breaking Load:** {cables.get('breaking_load', 0):.0f} kN")
        
        # Dome Data
        dome_data = design_results.get("dome_data", {})
        if dome_data:
            st.markdown("#### 🌍 Geodesic Dome Data")
            st.markdown(f"**Nodes:** {dome_data.get('num_nodes', 0)}")
            st.markdown(f"**Members:** {dome_data.get('num_members', 0)}")
            st.markdown(f"**Total Length:** {dome_data.get('total_length', 0):.1f} m")
            st.markdown(f"**Length Std Dev:** {dome_data.get('length_std_dev', 0):.3f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    elif report_type == "📊 Cost Report":
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown("### 💰 Cost Report")
        
        bq = design_results.get("bq", {})
        currency = get_currency(st.session_state.materials.get("country", "Malaysia"))
        
        st.markdown(f"**Currency:** {currency['code']} ({currency['symbol']})")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        col1.metric("Total Cost", f"{currency['symbol']}{bq.get('total_cost', 0):,.0f}")
        col2.metric("Steel Weight", f"{bq.get('total_steel_weight', 0):.0f} kg")
        
        col3, col4 = st.columns(2)
        col3.metric("Fabric Area", f"{bq.get('total_fabric_area', 0):.0f} m²")
        col4.metric("Joint Type", bq.get('joint_type', 'bolted').upper())
        
        if "items" in bq:
            st.markdown("---")
            st.markdown("#### 📋 Bill of Quantities")
            for item in bq["items"][:10]:
                st.markdown(f"**{item['item']}**")
                st.markdown(f"Qty: {item['qty']} {item['unit']} | Total: {currency['symbol']}{item['total_price']:,.0f}")
                if len(bq["items"]) > 10:
                    st.caption(f"... and {len(bq['items']) - 10} more items")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:  # Technical Report
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown("### 🔧 Technical Report")
        st.markdown("#### ✅ Design Checks")
        
        checks = design_results.get("all_checks", {})
        for check_name, check_data in checks.items():
            status = check_data["status"]
            if "✅" in status:
                color = "#2ecc71"
            else:
                color = "#f39c12"
            display_name = check_name.replace('_', ' ').title()
            st.markdown(f"<span style='color:{color}; font-weight:700;'>{status}</span> {display_name}: {check_data['value']}", unsafe_allow_html=True)
        
        st.markdown("---")
        score = design_results.get("health_score", 0)
        if score >= 80:
            status = "GOOD"
            color = "#2ecc71"
        elif score >= 60:
            status = "FAIR"
            color = "#f39c12"
        else:
            status = "POOR"
            color = "#e74c3c"
        
        st.markdown(f"### 🏥 Overall Health Score: **<span style='color:{color};font-size:2rem;'>{score}% - {status}</span>**", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to Workspace", key="reports_back_workspace", use_container_width=True, type="secondary"):
            st.session_state.page = "workspace"
            st.rerun()
    with col2:
        if st.button("📄 BQ & Costing", key="reports_to_bq", use_container_width=True, type="primary"):
            st.session_state.page = "bq"
            st.rerun()

# ============================================================
# WORKSPACE PAGE - ENHANCED WITH DYNAMIC INPUTS (Feature 2)
# ============================================================
def render_workspace():
    params, materials = st.session_state.params, st.session_state.materials
    info, typology = st.session_state.project_info, st.session_state.typology
    
    if typology not in GENERATORS and typology != "geodesic_dome":
        typology = "saddle_span"
    
    st.markdown("## 🧠 Design Workspace")
    st.caption(f"📌 {info.get('name', 'Untitled')} — {info.get('client', 'Unknown')}")
    
    # Get structure info
    structure_info = STRUCTURE_TYPES.get(typology, {})
    st.caption(f"📐 {structure_info.get('name', typology.replace('_', ' ').title())} | {structure_info.get('category', 'General')}")
    
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
        # Dynamic input form based on structure type (Feature 2)
        params, materials = get_structure_input_form(typology, params, materials, st.session_state.locked)
        
        # Common settings
        st.markdown('<div class="sds-card"><div class="title">🧱 Materials</div>', unsafe_allow_html=True)
        
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
        
        # Joint type (if applicable)
        if typology not in ["geodesic_dome", "cable_net", "tensile_membrane"]:
            joint_options = ["bolted", "welded"]
            joint_labels = ["🔩 Bolted (Pin Connection)", "⚡ Welded (Moment Connection)"]
            current_joint = materials.get("joint_type", "bolted")
            joint_idx = joint_options.index(current_joint) if current_joint in joint_options else 0
            selected_joint_label = st.selectbox(
                "Connection Type", 
                joint_labels, 
                index=joint_idx, 
                disabled=st.session_state.locked, 
                key="joint_type_workspace"
            )
            materials["joint_type"] = joint_options[joint_labels.index(selected_joint_label)]
            
            joint_desc = JOINT_MULTIPLIERS[materials["joint_type"]]["description"]
            st.markdown(f"<span style='color:#b0c4de;font-size:0.85rem;'>ℹ️ {joint_desc}</span>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Fabric selection for tensile structures
        if typology in ["saddle_span", "clear_span_tent", "tensile_membrane", "shade_structure"]:
            st.markdown('<div class="sds-card"><div class="title">🧵 Fabric</div>', unsafe_allow_html=True)
            fabric_options = ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"]
            materials["fabric_type"] = st.selectbox(
                "Fabric Material", 
                fabric_options, 
                index=fabric_options.index(materials.get("fabric_type", "PVC-coated Polyester")), 
                disabled=st.session_state.locked, 
                key="fabric_type_workspace"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Cable selection
        st.markdown('<div class="sds-card"><div class="title">🔗 Cables</div>', unsafe_allow_html=True)
        cable_options = ["6x19 Galvanized", "6x19 Stainless", "Polyester Rope"]
        materials["cable_type"] = st.selectbox(
            "Cable Type", 
            cable_options, 
            index=cable_options.index(materials.get("cable_type", "6x19 Galvanized")), 
            disabled=st.session_state.locked, 
            key="cable_type_workspace"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Location
        st.markdown('<div class="sds-card"><div class="title">🌍 Location</div>', unsafe_allow_html=True)
        countries = list(COUNTRY_CURRENCIES.keys())
        country_idx = countries.index(materials.get("country", "Malaysia")) if materials.get("country", "Malaysia") in countries else 0
        materials["country"] = st.selectbox("Country", countries, index=country_idx, disabled=st.session_state.locked, key="country_workspace")
        currency = get_currency(materials["country"])
        st.markdown(f"**Currency:** {currency['symbol']} ({currency['code']})")
        
        std_options = ["EU", "CN", "UK", "MY", "US"]
        materials["standard"] = st.selectbox("Design Standard", std_options, index=std_options.index(materials.get("standard", "EU")), disabled=st.session_state.locked, key="standard_workspace")
        badge_class = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(materials["standard"], "badge-eu")
        st.markdown(f'<span class="standard-badge {badge_class}">{materials["standard"]}</span> {get_standard_label(materials["standard"])}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Comments
        st.markdown('<div class="sds-card"><div class="title">💬 Notes</div>', unsafe_allow_html=True)
        st.session_state.comments = st.text_area("", st.session_state.comments, height=80, disabled=st.session_state.locked, key="comments_area_workspace")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Run Design Button
        if st.button("⚡ Run Design Analysis", key="workspace_run_analysis", use_container_width=True, type="primary"):
            with st.spinner("🔄 Calculating..."):
                st.session_state.design_results = {}
                st.session_state.bq = {}
                
                # Special handling for geodesic dome
                if typology == "geodesic_dome":
                    design_results = auto_design_structure(params, materials, typology)
                else:
                    design_results = auto_design_structure(params, materials, typology)
                
                st.session_state.design_results = design_results
                st.session_state.bq = design_results.get("bq", {})
                
                st.success("✅ Design analysis completed successfully!")
                st.rerun()
    
    with col_right:
        st.subheader("🔬 3D Model")
        
        # Choose appropriate generator
        if typology == "geodesic_dome":
            dome_params = {
                "radius": materials.get("dome_radius", 20),
                "frequency": materials.get("dome_frequency", 6),
                "height": materials.get("dome_height", 20)
            }
            fig = generate_geodesic_dome_3d(dome_params)
        elif typology in GENERATORS:
            fig = GENERATORS[typology](params, materials)
        else:
            fig = generate_simple_structure_3d(params, typology)
        
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        
        st.divider()
        
        # Display results if available
        if "design_results" in st.session_state and st.session_state.design_results:
            design_results = st.session_state.design_results
            
            st.markdown("## ⚡ Design Results")
            
            # Health Score
            score = design_results.get("health_score", 0)
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
            
            # Joint type badge
            joint_type = design_results.get("joint_type", "bolted")
            badge_color = "joint-weld" if joint_type == "welded" else "joint-bolt"
            st.markdown(f"<span class='joint-badge {badge_color}'>{joint_type.upper()} Connections</span>", unsafe_allow_html=True)
            
            # Loads
            st.markdown('<div class="sds-card">', unsafe_allow_html=True)
            st.markdown('<div class="title">📊 Loads</div>', unsafe_allow_html=True)
            loads = design_results["loads"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Wind", f"{loads['wind']:.1f} kN")
            c2.metric("Dead", f"{loads['dead']:.1f} kN")
            c3.metric("Total", f"{loads['total']:.1f} kN")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Member Selection
            beam = design_results.get("beams", {}).get("main")
            if beam:
                st.markdown('<div class="sds-card">', unsafe_allow_html=True)
                st.markdown('<div class="title">🔧 Member Selection</div>', unsafe_allow_html=True)
                sec_type = beam.get("section_type", materials.get("section_type", "CHS"))
                st.markdown(f"**Selected:** {beam['section']} {get_section_tag(sec_type)}")
                if beam.get("note"):
                    st.info(beam["note"])
                st.markdown(f"**Moment:** {beam['moment_capacity']:.1f} / {beam['required_moment']:.1f} kNm")
                if beam.get('is_adequate', False):
                    st.success("✅ Adequate")
                else:
                    st.warning("⚠️ Check")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Fabric & Cables
            fabric = design_results.get("fabric", {})
            cables = design_results.get("cables", {})
            if fabric or cables:
                st.markdown('<div class="sds-card">', unsafe_allow_html=True)
                st.markdown('<div class="title">🧵 Materials</div>', unsafe_allow_html=True)
                if fabric:
                    st.markdown(f"**Fabric:** {fabric.get('type', 'N/A')} ({fabric.get('thickness', 'N/A')}mm)")
                if cables:
                    st.markdown(f"**Cable:** {cables.get('type', 'N/A')} {cables.get('diameter', 'N/A')}mm")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Dome specific results
            dome_data = design_results.get("dome_data", {})
            if dome_data:
                st.markdown('<div class="sds-card">', unsafe_allow_html=True)
                st.markdown('<div class="title">🌍 Dome Statistics</div>', unsafe_allow_html=True)
                st.markdown(f"**Nodes:** {dome_data.get('num_nodes', 0)}")
                st.markdown(f"**Members:** {dome_data.get('num_members', 0)}")
                st.markdown(f"**Total Length:** {dome_data.get('total_length', 0):.1f} m")
                st.markdown(f"**Avg Length:** {dome_data.get('avg_length', 0):.2f} m")
                st.markdown(f"**Length Std Dev:** {dome_data.get('length_std_dev', 0):.3f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # BQ Quick View
            if st.session_state.bq:
                bq = st.session_state.bq
                currency = get_currency(materials.get("country", "Malaysia"))
                st.divider()
                col1, col2 = st.columns(2)
                col1.metric("Total Cost", f"{currency['symbol']}{bq.get('total_cost', 0):,.0f}")
                col2.metric("Steel Weight", f"{bq.get('total_steel_weight', 0):.0f} kg")
                if st.button("📄 View Full BQ", key="workspace_view_full_bq", use_container_width=True, type="primary"):
                    st.session_state.page = "bq"
                    st.rerun()
            
            # Export quick actions (Feature 5)
            st.divider()
            st.markdown("### 📤 Quick Export")
            export_cols = st.columns(3)
            
            with export_cols[0]:
                if st.button("📄 PDF", key="quick_pdf", use_container_width=True, type="secondary"):
                    pdf_buf = export_to_pdf(
                        design_results,
                        st.session_state.project_info,
                        st.session_state.materials
                    )
                    if pdf_buf:
                        st.download_button(
                            label="📥 Download",
                            data=pdf_buf,
                            file_name=f"Report_{st.session_state.project_info.get('reference', 'project')}.pdf",
                            mime="application/pdf",
                            key="quick_pdf_download"
                        )
            
            with export_cols[1]:
                if st.button("📊 CSV", key="quick_csv", use_container_width=True, type="secondary"):
                    csv_data = export_to_csv(design_results)
                    st.download_button(
                        label="📥 Download",
                        data=csv_data,
                        file_name=f"Results_{st.session_state.project_info.get('reference', 'project')}.csv",
                        mime="text/csv",
                        key="quick_csv_download"
                    )
            
            with export_cols[2]:
                if st.button("📦 ZIP", key="quick_zip", use_container_width=True, type="secondary"):
                    try:
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            pdf_buf = export_to_pdf(
                                design_results,
                                st.session_state.project_info,
                                st.session_state.materials
                            )
                            if pdf_buf:
                                zip_file.writestr(f"Report_{st.session_state.project_info.get('reference', 'project')}.pdf", pdf_buf.getvalue())
                            
                            csv_data = export_to_csv(design_results)
                            zip_file.writestr(f"Results_{st.session_state.project_info.get('reference', 'project')}.csv", csv_data)
                            
                            json_data = export_to_json(design_results)
                            zip_file.writestr(f"Results_{st.session_state.project_info.get('reference', 'project')}.json", json_data)
                        
                        zip_buffer.seek(0)
                        st.download_button(
                            label="📥 Download",
                            data=zip_buffer,
                            file_name=f"SDSe_Export_{st.session_state.project_info.get('reference', 'project')}.zip",
                            mime="application/zip",
                            key="quick_zip_download"
                        )
                    except Exception as e:
                        st.error(f"ZIP error: {str(e)}")
        
        else:
            st.info("💡 Adjust parameters and click 'Run Design Analysis' to see results")

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
st.caption("SDSe - Intelligent Fluid Design Workplace v7.0 | 25 Structure Types | 100+ Sections | 🔩/⚡ Joints | 🌍 Local Currency | 💡 Intelligent Engine")

# ============================================================
# REQUIREMENTS.TXT CONTENT (Feature 5 - For deployment)
# ============================================================
"""
streamlit>=1.28.0
plotly>=5.14.0
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
Pillow>=9.5.0
openpyxl>=3.1.0
"""
