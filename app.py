# =============================================================================
# SDSe — Intelligent Fluid Design Workplace
# Version 10.0 — Eurocode-Aligned (EN 1990 + EN 1991 + EN 1993 / MS EN)
# -----------------------------------------------------------------------------
# Platform : Streamlit Cloud (repo: sds-app, entrypoint: app.py)
# Standard : EN 1990 (basis), EN 1991 (actions), EN 1993 (steel design)
#            MS EN adopted for Malaysia. Optional EU / UK / CN / US overlays.
# Charter  : gamma_G = 1.35, gamma_Q = 1.50, gamma_M0 = 1.00,
#            gamma_M1 = 1.00, gamma_M2 = 1.20 (MY national annex)
# Health   : Computed from actual unity ratios. 100% only when ALL pass.
# Scope    : 6 structure families — saddle span, sail membrane, frame tents,
#            portal frame, single cone membrane, multiple cone membrane.
# Units    : mm-based section properties (A mm^2, I mm^4, W_el mm^3,
#            i mm, weight kg/m, depth mm).
# =============================================================================

import math
import json
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="SDSe — Intelligent Fluid Design Workplace",
    page_icon="⛺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# GLOBAL CSS — dark theme, accent orange #f39c12, background #0a0e17
# =============================================================================

st.markdown(
    """
    <style>
    :root {
        --sdse-bg:        #0a0e17;
        --sdse-panel:     #111827;
        --sdse-panel-2:   #1a2332;
        --sdse-accent:    #f39c12;
        --sdse-accent-2:  #f1c40f;
        --sdse-pass:      #2ecc71;
        --sdse-warn:      #f39c12;
        --sdse-fail:      #e74c3c;
        --sdse-text:      #e6edf3;
        --sdse-muted:     #8b949e;
        --sdse-border:    #2a3441;
    }
    .stApp { background: var(--sdse-bg); color: var(--sdse-text); }

    .sdse-card {
        background: var(--sdse-panel);
        border: 1px solid var(--sdse-border);
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.4);
    }
    .sdse-card h3 {
        margin: 0 0 8px 0; font-size: 0.95rem;
        color: var(--sdse-accent); letter-spacing: 0.3px;
    }

    .path-card {
        background: var(--sdse-panel-2);
        border-left: 4px solid var(--sdse-accent);
        border-radius: 6px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }
    .path-card .label { color: var(--sdse-muted); font-size: 0.75rem; text-transform: uppercase; }
    .path-card .value { color: var(--sdse-text); font-size: 1.05rem; font-weight: 600; }

    .health-score {
        font-size: 3.2rem; font-weight: 700;
        color: var(--sdse-accent); line-height: 1;
        text-align: center;
    }
    .health-score.pass  { color: var(--sdse-pass); }
    .health-score.warn  { color: var(--sdse-warn); }
    .health-score.fail  { color: var(--sdse-fail); }
    .health-score-label {
        text-align: center; color: var(--sdse-muted);
        font-size: 0.75rem; text-transform: uppercase;
        letter-spacing: 1px; margin-top: 4px;
    }

    .safety-box {
        background: var(--sdse-panel-2);
        border-radius: 6px; padding: 8px 10px;
        margin-bottom: 6px; font-size: 0.82rem;
        display: flex; justify-content: space-between;
        border-left: 3px solid var(--sdse-border);
    }
    .safety-box.pass { border-left-color: var(--sdse-pass); }
    .safety-box.warn { border-left-color: var(--sdse-warn); }
    .safety-box.fail { border-left-color: var(--sdse-fail); }
    .safety-box .ratio { font-weight: 600; }
    .safety-box .ratio.pass { color: var(--sdse-pass); }
    .safety-box .ratio.warn { color: var(--sdse-warn); }
    .safety-box .ratio.fail { color: var(--sdse-fail); }

    .member-recommend {
        background: linear-gradient(90deg, #1a2332 0%, #111827 100%);
        border: 1px solid var(--sdse-accent);
        border-radius: 8px; padding: 12px 14px;
        margin: 8px 0;
    }
    .member-recommend .title {
        color: var(--sdse-accent); font-weight: 600;
        font-size: 0.9rem; margin-bottom: 4px;
    }
    .member-recommend .spec {
        color: var(--sdse-text); font-size: 1.1rem;
        font-weight: 600; font-family: monospace;
    }

    .sdse-topnav {
        display: flex; gap: 6px; flex-wrap: wrap;
        padding: 8px 0; margin-bottom: 14px;
        border-bottom: 1px solid var(--sdse-border);
    }
    .sdse-topnav .nav-item {
        padding: 6px 14px; border-radius: 6px;
        background: var(--sdse-panel); color: var(--sdse-muted);
        font-size: 0.85rem; cursor: pointer;
        border: 1px solid var(--sdse-border);
    }
    .sdse-topnav .nav-item.active {
        background: var(--sdse-accent); color: #0a0e17;
        font-weight: 600; border-color: var(--sdse-accent);
    }

    .sdse-badge {
        display: inline-block; padding: 2px 8px;
        border-radius: 10px; font-size: 0.7rem;
        font-weight: 600; margin-right: 4px;
    }
    .sdse-badge.ec { background: #f39c1233; color: var(--sdse-accent); border: 1px solid var(--sdse-accent); }
    .sdse-badge.my { background: #2ecc7133; color: var(--sdse-pass); border: 1px solid var(--sdse-pass); }

    .sdse-divider { height: 1px; background: var(--sdse-border); margin: 14px 0; }
    .sdse-muted { color: var(--sdse-muted); font-size: 0.8rem; }

    div[data-testid="stMetricValue"] { color: var(--sdse-accent); }
    div[data-testid="stSidebar"] { background: var(--sdse-panel); }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    if "project_info" not in st.session_state:
        st.session_state.project_info = {
            "name": "Untitled Project",
            "ref": "SDSe-0001",
            "engineer": "",
            "client": "",
            "location": "",
            "revision": "A",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "",
        }

    if "params" not in st.session_state:
        st.session_state.params = {
            "A": 20.0,
            "B": 12.0,
            "LAA": 0.0,
        }

    if "materials" not in st.session_state:
        st.session_state.materials = {
            "standard": "MY",
            "section_type": "CHS",
            "member_type": "Primary",
            "joint_type": "Welded",
            "cable_type": "Strand",
            "fabric_type": "PVDF",
            "num_bays": 1,
        }

    if "results" not in st.session_state:
        st.session_state.results = None
    if "health_score" not in st.session_state:
        st.session_state.health_score = 0.0
    if "check_log" not in st.session_state:
        st.session_state.check_log = []
    if "selected_section" not in st.session_state:
        st.session_state.selected_section = None
    if "selected_cable" not in st.session_state:
        st.session_state.selected_cable = None
    if "selected_fabric" not in st.session_state:
        st.session_state.selected_fabric = None
    if "bq_rows" not in st.session_state:
        st.session_state.bq_rows = []
    if "registered_projects" not in st.session_state:
        st.session_state.registered_projects = []
    if "active_nav" not in st.session_state:
        st.session_state.active_nav = "Dashboard"


init_session_state()

# =============================================================================
# CONSTANTS
# =============================================================================

WIND_SPEEDS = {
    "EU": 30.0,
    "CN": 28.0,
    "UK": 26.0,
    "MY": 33.5,
    "US": 38.0,
}

PARTIAL_FACTORS = {
    "gamma_G":      1.35,
    "gamma_Q_wind": 1.50,
    "gamma_M0":     1.00,
    "gamma_M1":     1.00,
    "gamma_M2":     1.20,
}

STEEL_MATERIALS = {
    "Steel": {
        "S235": {"fy": 235, "fu": 360, "E": 210000, "rho": 7850},
        "S275": {"fy": 275, "fu": 430, "E": 210000, "rho": 7850},
        "S355": {"fy": 355, "fu": 510, "E": 210000, "rho": 7850},
        "S420": {"fy": 420, "fu": 520, "E": 210000, "rho": 7850},
        "S460": {"fy": 460, "fu": 540, "E": 210000, "rho": 7850},
        "default": "S355",
    },
    "Aluminum": {
        "6061-T6": {"fy": 240, "fu": 290, "E": 69000, "rho": 2700},
        "6082-T6": {"fy": 250, "fu": 295, "E": 70000, "rho": 2700},
        "default": "6061-T6",
    },
    "Wood": {
        "GL24h":  {"fy": 24,  "fu": 24,  "E": 11000, "rho": 420},
        "GL28h":  {"fy": 28,  "fu": 28,  "E": 12600, "rho": 440},
        "C24":    {"fy": 24,  "fu": 24,  "E": 11000, "rho": 420},
        "default": "GL28h",
    },
    "Composite": {
        "GFRP":   {"fy": 300, "fu": 500, "E": 30000, "rho": 1800},
        "CFRP":   {"fy": 800, "fu": 1200, "E": 120000, "rho": 1600},
        "default": "GFRP",
    },
}

FABRIC_PROPERTIES = {
    "PVDF": {
        "Type I":   {"f_u_warp": 60,  "f_u_weft": 55,  "E_warp": 800,  "E_weft": 700,  "t_mm": 0.6, "kg_m2": 0.6},
        "Type II":  {"f_u_warp": 80,  "f_u_weft": 70,  "E_warp": 1000, "E_weft": 900,  "t_mm": 0.7, "kg_m2": 0.7},
        "Type III": {"f_u_warp": 100, "f_u_weft": 90,  "E_warp": 1200, "E_weft": 1000, "t_mm": 0.8, "kg_m2": 0.9},
        "Type IV":  {"f_u_warp": 120, "f_u_weft": 110, "E_warp": 1400, "E_weft": 1200, "t_mm": 0.9, "kg_m2": 1.1},
        "default": "Type III",
    },
    "PTFE": {
        "Type A": {"f_u_warp": 140, "f_u_weft": 120, "E_warp": 1500, "E_weft": 1300, "t_mm": 0.8, "kg_m2": 1.2},
        "Type B": {"f_u_warp": 160, "f_u_weft": 140, "E_warp": 1700, "E_weft": 1500, "t_mm": 1.0, "kg_m2": 1.5},
        "default": "Type A",
    },
    "ETFE": {
        "250um": {"f_u_warp": 52, "f_u_weft": 52, "E_warp": 900, "E_weft": 900, "t_mm": 0.25, "kg_m2": 0.44},
        "200um": {"f_u_warp": 50, "f_u_weft": 50, "E_warp": 850, "E_weft": 850, "t_mm": 0.20, "kg_m2": 0.35},
        "default": "250um",
    },
}

CABLE_PROPERTIES = {
    "Strand": {
        "6mm":  {"d": 6.0,  "A": 22.9,  "f_u": 1770, "E": 160000, "kg_m": 0.180},
        "8mm":  {"d": 8.0,  "A": 40.7,  "f_u": 1770, "E": 160000, "kg_m": 0.320},
        "10mm": {"d": 10.0, "A": 63.6,  "f_u": 1770, "E": 160000, "kg_m": 0.500},
        "12mm": {"d": 12.0, "A": 91.6,  "f_u": 1770, "E": 160000, "kg_m": 0.720},
        "14mm": {"d": 14.0, "A": 124.7, "f_u": 1770, "E": 160000, "kg_m": 0.980},
        "16mm": {"d": 16.0, "A": 162.9, "f_u": 1770, "E": 160000, "kg_m": 1.280},
        "18mm": {"d": 18.0, "A": 206.2, "f_u": 1770, "E": 160000, "kg_m": 1.620},
        "20mm": {"d": 20.0, "A": 254.6, "f_u": 1770, "E": 160000, "kg_m": 2.000},
        "22mm": {"d": 22.0, "A": 308.0, "f_u": 1770, "E": 160000, "kg_m": 2.420},
        "24mm": {"d": 24.0, "A": 366.6, "f_u": 1770, "E": 160000, "kg_m": 2.880},
        "default": "16mm",
    },
    "Locked Coil": {
        "40mm": {"d": 40.0, "A": 980.0,  "f_u": 1570, "E": 160000, "kg_m": 7.70},
        "50mm": {"d": 50.0, "A": 1530.0, "f_u": 1570, "E": 160000, "kg_m": 12.00},
        "60mm": {"d": 60.0, "A": 2200.0, "f_u": 1570, "E": 160000, "kg_m": 17.30},
        "default": "50mm",
    },
    "Spiral": {
        "12mm": {"d": 12.0, "A": 85.0,  "f_u": 1570, "E": 160000, "kg_m": 0.67},
        "16mm": {"d": 16.0, "A": 150.0, "f_u": 1570, "E": 160000, "kg_m": 1.18},
        "20mm": {"d": 20.0, "A": 235.0, "f_u": 1570, "E": 160000, "kg_m": 1.85},
        "default": "16mm",
    },
}

# =============================================================================
# STRUCTURE TYPES — 6 EXACT FAMILIES
# =============================================================================

STRUCTURE_TYPES = {
    "Saddle Span": {
        "family": "tensile",
        "primary_action": "tension",
        "default_A": 20.0,
        "default_B": 12.0,
        "default_LAA": 0.0,
        "load_paths": ["Fabric", "Edge Cable", "Mast", "Anchor"],
        "governing_limit": "Fabric stress + edge cable tension",
    },
    "Sail Membrane Roof": {
        "family": "tensile",
        "primary_action": "tension",
        "default_A": 15.0,
        "default_B": 10.0,
        "default_LAA": 0.0,
        "load_paths": ["Fabric", "Ridge Cable", "Valley Cable", "Mast"],
        "governing_limit": "Fabric stress + cable tension",
    },
    "Frame Tents": {
        "family": "frame",
        "primary_action": "combined",
        "default_A": 8.0,
        "default_B": 6.0,
        "default_LAA": 0.0,
        "load_paths": ["Frame", "Fabric", "Base Plate"],
        "governing_limit": "Frame bending + buckling",
    },
    "Portal Frame": {
        "family": "frame",
        "primary_action": "combined",
        "default_A": 20.0,
        "default_B": 12.0,
        "default_LAA": 6.0,
        "load_paths": ["Rafter", "Column", "Base", "Purlin"],
        "governing_limit": "Bending + buckling + deflection",
    },
    "Single Cone Membrane Roof": {
        "family": "tensile",
        "primary_action": "tension",
        "default_A": 12.0,
        "default_B": 12.0,
        "default_LAA": 0.0,
        "load_paths": ["Fabric", "Ring Cable", "Mast", "Anchor"],
        "governing_limit": "Fabric stress + ring cable tension",
    },
    "Multiple Cone Membrane Roof": {
        "family": "tensile",
        "primary_action": "tension",
        "default_A": 30.0,
        "default_B": 20.0,
        "default_LAA": 0.0,
        "load_paths": ["Fabric", "Ring Cable", "Mast", "Anchor", "Valley Cable"],
        "governing_limit": "Fabric stress + ring cable tension + mast buckling",
    },
}

# =============================================================================
# SECTION PROPERTIES — exact user-supplied dict
# Units: A mm^2, I mm^4, W_el mm^3, i mm, weight kg/m, depth mm
# =============================================================================

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
    "SHS 100x100x5": {"A": 1900, "I": 2.8e6, "W_el": 56.0e3, "i": 38.4, "weight": 14.9, "type": "SHS", "depth": 100},
    "SHS 150x150x6": {"A": 3456, "I": 11.9e6, "W_el": 159e3, "i": 58.7, "weight": 27.1, "type": "SHS", "depth": 150},
    "SHS 200x200x8": {"A": 6144, "I": 36.0e6, "W_el": 360e3, "i": 76.5, "weight": 48.2, "type": "SHS", "depth": 200},
    "SHS 300x300x12": {"A": 13824, "I": 182e6, "W_el": 1213e3, "i": 114.8, "weight": 108.5, "type": "SHS", "depth": 300},
    "RHS 100x50x4": {"A": 1136, "I": 1.4e6, "W_el": 28.0e3, "i": 35.1, "weight": 8.9, "type": "RHS", "depth": 100},
    "RHS 150x100x6": {"A": 2784, "I": 8.3e6, "W_el": 111e3, "i": 54.6, "weight": 21.8, "type": "RHS", "depth": 150},
    "RHS 200x100x8": {"A": 4608, "I": 21.2e6, "W_el": 212e3, "i": 67.8, "weight": 36.2, "type": "RHS", "depth": 200},
    "RHS 300x200x12": {"A": 11424, "I": 156e6, "W_el": 1040e3, "i": 116.8, "weight": 89.7, "type": "RHS", "depth": 300},
    "I-100": {"A": 1030, "I": 4.5e6, "W_el": 90e3, "i": 66.1, "weight": 8.1, "type": "I-Beam", "depth": 100},
    "I-200": {"A": 3310, "I": 38.0e6, "W_el": 380e3, "i": 107.1, "weight": 26.0, "type": "I-Beam", "depth": 200},
    "I-300": {"A": 6720, "I": 136.0e6, "W_el": 907e3, "i": 142.3, "weight": 52.8, "type": "I-Beam", "depth": 300},
    "I-400": {"A": 11800, "I": 348.0e6, "W_el": 1740e3, "i": 171.8, "weight": 92.6, "type": "I-Beam", "depth": 400},
    "I-500": {"A": 17500, "I": 694.0e6, "W_el": 2780e3, "i": 199.2, "weight": 137.4, "type": "I-Beam", "depth": 500},
    "L50x50x5": {"A": 480, "I": 0.18e6, "W_el": 5.1e3, "i": 19.4, "weight": 3.8, "type": "Angle", "depth": 50},
    "L100x100x10": {"A": 1910, "I": 2.28e6, "W_el": 32.0e3, "i": 34.5, "weight": 15.0, "type": "Angle", "depth": 100},
    "C100x50x6": {"A": 1010, "I": 2.8e6, "W_el": 56e3, "i": 52.6, "weight": 7.9, "type": "Channel", "depth": 100},
    "C200x90x10": {"A": 2890, "I": 24.0e6, "W_el": 240e3, "i": 91.1, "weight": 22.7, "type": "Channel", "depth": 200},
    "C250x100x12": {"A": 3930, "I": 48.0e6, "W_el": 384e3, "i": 110.5, "weight": 30.8, "type": "Channel", "depth": 250},
}


def get_catalogue(section_type):
    """Return list of section names filtered by type from SECTION_PROPERTIES."""
    return [k for k, v in SECTION_PROPERTIES.items() if v.get("type") == section_type]


def get_section(name):
    """Return the section dict for a given name, or None."""
    return SECTION_PROPERTIES.get(name)


# =============================================================================
# ENGINEERING — WIND LOAD (EN 1991-1-4 enshrined)
# =============================================================================

def calculate_wind_load_enshrined(span, apex, rise, standard):
    """
    EN 1991-1-4 peak velocity pressure q_p(z) applied to a curved/duopitch
    roof envelope, returning net uplift and pressure in kPa.
    """
    vb = WIND_SPEEDS.get(standard, 30.0)

    z = max(apex, rise, 0.0) + 3.0

    z0 = 0.05
    zmin = 2.0
    z_eff = max(z, zmin)
    kr = 0.19 * (z0 / 0.05) ** 0.07
    cr = kr * math.log(z_eff / z0)

    Iv = 1.0 / math.log(z_eff / z0)

    ce = (1.0 + 7.0 * Iv) * (cr ** 2)

    rho = 1.25
    qb = 0.5 * rho * (vb ** 2)

    qp = ce * qb / 1000.0

    cpe_uplift = -1.20
    cpe_pressure = 0.80
    cpi = 0.20

    uplift = qp * (cpe_uplift - cpi)
    pressure = qp * (cpe_pressure - cpi)

    return {
        "vb_ms": vb,
        "q_p_kpa": qp,
        "uplift_kpa": uplift,
        "pressure_kpa": pressure,
        "ce": ce,
        "cr": cr,
        "Iv": Iv,
        "z": z,
    }


# =============================================================================
# ENGINEERING — DEAD LOAD
# =============================================================================

def calculate_dead_load_single(params, materials):
    """
    Self-weight of a single structural unit (roof bay / span).
    """
    A = float(params.get("A", 20.0))
    B = float(params.get("B", 12.0))
    LAA = float(params.get("LAA", 0.0))

    section_type = materials.get("section_type", "CHS")
    member_type = materials.get("member_type", "Primary")
    fabric_type = materials.get("fabric_type", "PVDF")

    fabric_kg = 0.9
    if fabric_type in FABRIC_PROPERTIES:
        default_key = FABRIC_PROPERTIES[fabric_type].get("default")
        if default_key and default_key in FABRIC_PROPERTIES[fabric_type]:
            fabric_kg = FABRIC_PROPERTIES[fabric_type][default_key]["kg_m2"]
    gk_fabric = fabric_kg * 9.81 / 1000.0

    frame_kg_per_m = 20.0
    if section_type == "SHS":
        frame_kg_per_m = 22.0
    elif section_type == "RHS":
        frame_kg_per_m = 24.0
    elif section_type == "I-Beam":
        frame_kg_per_m = 30.0
    elif section_type == "Angle":
        frame_kg_per_m = 12.0
    elif section_type == "Channel":
        frame_kg_per_m = 22.0

    if member_type == "Secondary":
        frame_kg_per_m *= 0.7
    elif member_type == "Bracing":
        frame_kg_per_m *= 0.5

    total_length_est = (A + B) * 2.0 + LAA * 2.0
    gk_frame_kn = frame_kg_per_m * total_length_est * 9.81 / 1000.0

    plan_area = A * B
    if plan_area <= 0:
        plan_area = 1.0

    gk_roof_kn = gk_fabric * plan_area
    total_gk_kn = gk_frame_kn + gk_roof_kn

    return {
        "gk_fabric_kpa": gk_fabric,
        "gk_frame_kn": gk_frame_kn,
        "gk_roof_kn": gk_roof_kn,
        "total_gk_kn": total_gk_kn,
        "plan_area_m2": plan_area,
        "total_length_est_m": total_length_est,
    }


# =============================================================================
# ENGINEERING — ULS COMBINATION (EN 1990 §6.4.3 Eq. 6.10)
# =============================================================================

def get_uls_combination(Gk, Qk_wind, Qk_live, standard):
    """
    EN 1990 Eq. (6.10) — ULS combination.
    """
    gG = PARTIAL_FACTORS["gamma_G"]
    gQ = PARTIAL_FACTORS["gamma_Q_wind"]

    psi0_wind = 0.6
    psi0_live = 0.7

    gravity_kn = gG * Gk + gQ * Qk_live

    uplift_kn = gG * Gk + gQ * Qk_wind + gQ * psi0_live * Qk_live

    if abs(uplift_kn) > abs(gravity_kn):
        governing_kn = uplift_kn
        governing_case = "Uplift"
    else:
        governing_kn = gravity_kn
        governing_case = "Gravity"

    return {
        "gravity_kn": gravity_kn,
        "uplift_kn": uplift_kn,
        "governing_kn": governing_kn,
        "governing_case": governing_case,
        "gamma_G": gG,
        "gamma_Q": gQ,
        "psi0_wind": psi0_wind,
        "psi0_live": psi0_live,
    }


# ============================== CHUNK 1 END ==================================

# =============================================================================
# ENGINEERING — CHECK FUNCTIONS (EN 1993-1-1 / MS EN)
# All inputs in N, Nmm, mm, MPa. Section props from SECTION_PROPERTIES.
# =============================================================================

def _fy_from_materials(materials):
    """Return yield strength fy (MPa). Default S355."""
    family = "Steel"
    grade = STEEL_MATERIALS[family].get("default", "S355")
    return STEEL_MATERIALS[family][grade]["fy"]


def _E_from_materials(materials):
    """Return Young's modulus E (MPa). Default steel."""
    family = "Steel"
    grade = STEEL_MATERIALS[family].get("default", "S355")
    return STEEL_MATERIALS[family][grade]["E"]


def check_bending(section_name, M_Ed_kNm, materials):
    """
    EN 1993-1-1 §6.2.5 — bending resistance of cross-section.
    M_Ed_kNm : design bending moment (kNm).
    Returns dict with ratio, Mc_Rd_kNm, status.
    """
    sec = SECTION_PROPERTIES.get(section_name)
    if sec is None:
        return {"ratio": 1e9, "Mc_Rd_kNm": 0.0, "status": "fail", "note": "section not found"}

    fy = _fy_from_materials(materials)
    gM0 = PARTIAL_FACTORS["gamma_M0"]

    W_el_mm3 = sec["W_el"]
    Mc_Rd_Nmm = W_el_mm3 * fy / gM0
    Mc_Rd_kNm = Mc_Rd_Nmm / 1.0e6

    if Mc_Rd_kNm <= 0:
        ratio = 1e9
    else:
        ratio = abs(M_Ed_kNm) / Mc_Rd_kNm

    status = "pass" if ratio <= 1.0 else ("warn" if ratio <= 1.05 else "fail")
    return {
        "ratio": ratio,
        "Mc_Rd_kNm": Mc_Rd_kNm,
        "status": status,
        "fy": fy,
        "W_el_mm3": W_el_mm3,
    }


def check_compression_buckling(section_name, N_Ed_kN, L_cr_m, materials):
    """
    EN 1993-1-1 §6.3.1 — flexural buckling of compression members.
    N_Ed_kN : design axial compression (kN, positive).
    L_cr_m  : buckling length (m).
    """
    sec = SECTION_PROPERTIES.get(section_name)
    if sec is None:
        return {"ratio": 1e9, "Nb_Rd_kN": 0.0, "status": "fail", "note": "section not found"}

    fy = _fy_from_materials(materials)
    E = _E_from_materials(materials)
    gM1 = PARTIAL_FACTORS["gamma_M1"]

    A_mm2 = sec["A"]
    I_mm4 = sec["I"]
    i_mm = sec["i"]
    sec_type = sec["type"]

    L_cr_mm = L_cr_m * 1000.0
    if i_mm <= 0:
        lam = 1e9
    else:
        lam = L_cr_mm / i_mm

    if L_cr_mm <= 0:
        Ncr_N = 1e12
    else:
        Ncr_N = (math.pi ** 2) * E * I_mm4 / (L_cr_mm ** 2)

    if Ncr_N <= 0:
        lam_bar = 1e9
    else:
        lam_bar = math.sqrt(A_mm2 * fy / Ncr_N)

    if sec_type in ("CHS", "SHS", "RHS"):
        alpha = 0.21
    elif sec_type in ("I-Beam", "Channel"):
        alpha = 0.34
    else:
        alpha = 0.49

    if lam_bar <= 0.2:
        chi = 1.0
    else:
        phi = 0.5 * (1.0 + alpha * (lam_bar - 0.2) + lam_bar ** 2)
        if phi <= 0:
            chi = 0.0
        else:
            chi = 1.0 / (phi + math.sqrt(max(phi ** 2 - lam_bar ** 2, 0.0)))
        chi = min(chi, 1.0)

    Nb_Rd_N = chi * A_mm2 * fy / gM1
    Nb_Rd_kN = Nb_Rd_N / 1000.0

    if Nb_Rd_kN <= 0:
        ratio = 1e9
    else:
        ratio = abs(N_Ed_kN) / Nb_Rd_kN

    status = "pass" if ratio <= 1.0 else ("warn" if ratio <= 1.05 else "fail")
    return {
        "ratio": ratio,
        "Nb_Rd_kN": Nb_Rd_kN,
        "chi": chi,
        "lam_bar": lam_bar,
        "Ncr_kN": Ncr_N / 1000.0,
        "status": status,
    }


def check_tension(section_name, N_Ed_kN, materials):
    """
    EN 1993-1-1 §6.2.3 — tension resistance of gross cross-section.
    """
    sec = SECTION_PROPERTIES.get(section_name)
    if sec is None:
        return {"ratio": 1e9, "Nt_Rd_kN": 0.0, "status": "fail", "note": "section not found"}

    fy = _fy_from_materials(materials)
    gM0 = PARTIAL_FACTORS["gamma_M0"]

    A_mm2 = sec["A"]
    Nt_Rd_N = A_mm2 * fy / gM0
    Nt_Rd_kN = Nt_Rd_N / 1000.0

    if Nt_Rd_kN <= 0:
        ratio = 1e9
    else:
        ratio = abs(N_Ed_kN) / Nt_Rd_kN

    status = "pass" if ratio <= 1.0 else ("warn" if ratio <= 1.05 else "fail")
    return {
        "ratio": ratio,
        "Nt_Rd_kN": Nt_Rd_kN,
        "status": status,
    }


def check_shear(section_name, V_Ed_kN, materials):
    """
    EN 1993-1-1 §6.2.6 — shear resistance.
    Vpl_Rd = A_v * fy / (sqrt(3) * gamma_M0).
    """
    sec = SECTION_PROPERTIES.get(section_name)
    if sec is None:
        return {"ratio": 1e9, "Vpl_Rd_kN": 0.0, "status": "fail", "note": "section not found"}

    fy = _fy_from_materials(materials)
    gM0 = PARTIAL_FACTORS["gamma_M0"]

    A_mm2 = sec["A"]
    sec_type = sec["type"]

    if sec_type in ("CHS", "SHS", "RHS", "I-Beam"):
        A_v = 0.6 * A_mm2
    else:
        A_v = A_mm2

    Vpl_Rd_N = A_v * fy / (math.sqrt(3.0) * gM0)
    Vpl_Rd_kN = Vpl_Rd_N / 1000.0

    if Vpl_Rd_kN <= 0:
        ratio = 1e9
    else:
        ratio = abs(V_Ed_kN) / Vpl_Rd_kN

    status = "pass" if ratio <= 1.0 else ("warn" if ratio <= 1.05 else "fail")
    return {
        "ratio": ratio,
        "Vpl_Rd_kN": Vpl_Rd_kN,
        "A_v_mm2": A_v,
        "status": status,
    }


def check_deflection(section_name, M_Ed_kNm, L_m, materials, limit_ratio=250.0):
    """
    SLS deflection check — simply-supported approximation.
    delta ≈ M * L^2 / (12 * E * I).
    limit_ratio: L / delta allowable (default 250 for roofs).
    """
    sec = SECTION_PROPERTIES.get(section_name)
    if sec is None:
        return {"ratio": 1e9, "delta_mm": 0.0, "delta_lim_mm": 0.0,
                "status": "fail", "note": "section not found"}

    E = _E_from_materials(materials)
    I_mm4 = sec["I"]

    M_Nmm = abs(M_Ed_kNm) * 1.0e6
    L_mm = L_m * 1000.0

    if E <= 0 or I_mm4 <= 0:
        delta_mm = 1e9
    else:
        delta_mm = M_Nmm * (L_mm ** 2) / (12.0 * E * I_mm4)

    delta_lim_mm = L_mm / limit_ratio

    if delta_lim_mm <= 0:
        ratio = 1e9
    else:
        ratio = delta_mm / delta_lim_mm

    status = "pass" if ratio <= 1.0 else ("warn" if ratio <= 1.05 else "fail")
    return {
        "ratio": ratio,
        "delta_mm": delta_mm,
        "delta_lim_mm": delta_lim_mm,
        "status": status,
    }


# =============================================================================
# ENGINEERING — SECTION SELECTION / AUTO-DESIGN
# =============================================================================

def select_optimal_section(section_type, M_Ed_kNm, N_Ed_kN, V_Ed_kN, L_m,
                           materials, limit_ratio=250.0):
    """
    Iterate SECTION_PROPERTIES filtered by type; return the lightest
    section that passes bending + buckling + tension + shear + deflection.
    """
    candidates = get_catalogue(section_type)
    if not candidates:
        candidates = list(SECTION_PROPERTIES.keys())

    candidates_sorted = sorted(
        candidates,
        key=lambda n: SECTION_PROPERTIES[n].get("weight", 1e9),
    )

    chosen = None
    report = []
    for name in candidates_sorted:
        b = check_bending(name, M_Ed_kNm, materials)
        c = check_compression_buckling(name, N_Ed_kN, L_m, materials)
        t = check_tension(name, N_Ed_kN, materials)
        s = check_shear(name, V_Ed_kN, materials)
        d = check_deflection(name, M_Ed_kNm, L_m, materials, limit_ratio)

        worst = max(b["ratio"], c["ratio"], t["ratio"], s["ratio"], d["ratio"])
        report.append({
            "name": name,
            "weight": SECTION_PROPERTIES[name].get("weight", 0.0),
            "bending": b["ratio"],
            "buckling": c["ratio"],
            "tension": t["ratio"],
            "shear": s["ratio"],
            "deflection": d["ratio"],
            "worst": worst,
        })

        if worst <= 1.0 and chosen is None:
            chosen = name
            break

    if chosen is None:
        best = min(report, key=lambda r: r["worst"])
        chosen = best["name"]

    return {
        "section": chosen,
        "report": report,
    }


def compute_health(check_results):
    """
    Health score from actual unity ratios.
    100% only when every check has ratio <= 1.0.
    """
    if not check_results:
        return 0.0, "fail"

    ratios = []
    for key, val in check_results.items():
        if isinstance(val, dict) and "ratio" in val:
            ratios.append(val["ratio"])

    if not ratios:
        return 0.0, "fail"

    overstress_sum = 0.0
    for r in ratios:
        if r > 1.0:
            overstress_sum += (r - 1.0) * 100.0

    mean_over = overstress_sum / len(ratios)
    score = max(0.0, 100.0 - mean_over)

    if score >= 95.0 and all(r <= 1.0 for r in ratios):
        status = "pass"
    elif score >= 70.0:
        status = "warn"
    else:
        status = "fail"

    return round(score, 1), status


def auto_design_structure(params, materials, structure_type, load_case=None):
    """
    Full design pipeline:
      1. Wind (uplift + pressure) and dead load.
      2. ULS gravity and uplift combinations.
      3. Approximate internal actions for the family.
      4. Auto-select optimal section.
      5. Run all checks on selected section.
      6. Compute health score.
    """
    A = float(params.get("A", 20.0))
    B = float(params.get("B", 12.0))
    LAA = float(params.get("LAA", 0.0))
    standard = materials.get("standard", "MY")
    section_type = materials.get("section_type", "CHS")
    num_bays = int(materials.get("num_bays", 1))

    stype = STRUCTURE_TYPES.get(structure_type, STRUCTURE_TYPES["Saddle Span"])
    family = stype["family"]

    span = max(A, B)
    apex = max(A, B) * 0.10
    rise = apex

    wind = calculate_wind_load_enshrined(span, apex, rise, standard)
    dead = calculate_dead_load_single(params, materials)

    plan_area = dead["plan_area_m2"]
    Gk_kn = dead["total_gk_kn"]

    qk_wind_uplift_kn = wind["uplift_kpa"] * plan_area
    qk_wind_press_kn = wind["pressure_kpa"] * plan_area
    qk_live_kn = 0.6 * plan_area

    combo = get_uls_combination(Gk_kn, qk_wind_press_kn, qk_live_kn, standard)

    if family == "tensile":
        N_Ed_kN = abs(combo["governing_kn"]) * 0.5
        M_Ed_kNm = abs(combo["governing_kn"]) * span / 20.0
        V_Ed_kN = abs(combo["governing_kn"]) * 0.15
    elif family == "frame":
        N_Ed_kN = abs(combo["governing_kn"]) * 0.25
        M_Ed_kNm = abs(combo["governing_kn"]) * span / 8.0
        V_Ed_kN = abs(combo["governing_kn"]) * 0.50
    else:
        N_Ed_kN = abs(combo["governing_kn"]) * 0.4
        M_Ed_kNm = abs(combo["governing_kn"]) * span / 12.0
        V_Ed_kN = abs(combo["governing_kn"]) * 0.25

    if num_bays > 1:
        N_Ed_kN /= num_bays
        M_Ed_kNm /= num_bays
        V_Ed_kN /= num_bays

    sel = select_optimal_section(
        section_type, M_Ed_kNm, N_Ed_kN, V_Ed_kN, span, materials
    )
    chosen = sel["section"]

    b = check_bending(chosen, M_Ed_kNm, materials)
    c = check_compression_buckling(chosen, N_Ed_kN, span, materials)
    t = check_tension(chosen, N_Ed_kN, materials)
    s = check_shear(chosen, V_Ed_kN, materials)
    d = check_deflection(chosen, M_Ed_kNm, span, materials)

    checks = {
        "bending": b,
        "buckling": c,
        "tension": t,
        "shear": s,
        "deflection": d,
    }

    health, health_status = compute_health(checks)

    return {
        "structure_type": structure_type,
        "family": family,
        "span_m": span,
        "plan_area_m2": plan_area,
        "wind": wind,
        "dead": dead,
        "combo": combo,
        "actions": {
            "N_Ed_kN": N_Ed_kN,
            "M_Ed_kNm": M_Ed_kNm,
            "V_Ed_kN": V_Ed_kN,
        },
        "selected_section": chosen,
        "checks": checks,
        "health": health,
        "health_status": health_status,
        "selection_report": sel["report"],
    }


# =============================================================================
# BILL OF QUANTITIES
# =============================================================================

def generate_bill_of_quantities(results, materials):
    """
    Produce a list of BQ rows from a design result.
    Each row: description, unit, qty, rate, amount.
    """
    if not results:
        return []

    rows = []
    chosen = results.get("selected_section")
    sec = SECTION_PROPERTIES.get(chosen, {})
    weight_kg_m = sec.get("weight", 0.0)
    family = results.get("family", "frame")
    span = results.get("span_m", 0.0)
    plan_area = results.get("plan_area_m2", 0.0)

    total_length_m = span * 4.0 if family == "frame" else span * 2.0
    steel_kg = total_length_m * weight_kg_m
    steel_tonne = steel_kg / 1000.0
    rows.append({
        "description": "Structural steel — " + str(chosen),
        "unit": "tonne",
        "qty": round(steel_tonne, 3),
        "rate": 8500.0,
        "amount": round(steel_tonne * 8500.0, 2),
    })

    if family == "tensile":
        fabric_m2 = plan_area * 1.15
        rows.append({
            "description": "Tensile membrane fabric (PVDF/PTFE)",
            "unit": "m2",
            "qty": round(fabric_m2, 1),
            "rate": 220.0,
            "amount": round(fabric_m2 * 220.0, 2),
        })

    if family in ("tensile", "cable"):
        cable_length_m = span * 2.5
        rows.append({
            "description": "Structural cable / strand",
            "unit": "m",
            "qty": round(cable_length_m, 1),
            "rate": 85.0,
            "amount": round(cable_length_m * 85.0, 2),
        })

    n_bases = 4 if family == "frame" else 6
    rows.append({
        "description": "Base plates and anchor bolts",
        "unit": "nr",
        "qty": n_bases,
        "rate": 450.0,
        "amount": round(n_bases * 450.0, 2),
    })

    paint_area = total_length_m * 1.5
    rows.append({
        "description": "Surface protection (galvanising + paint)",
        "unit": "m2",
        "qty": round(paint_area, 1),
        "rate": 45.0,
        "amount": round(paint_area * 45.0, 2),
    })

    return rows


# =============================================================================
# 3D GENERATORS (Plotly)
# =============================================================================

def generate_curved_beam_3d(span, rise, num_points=60):
    """
    Plotly Figure — parabolic curved beam (arch) in 3D.
    """
    x = np.linspace(-span / 2.0, span / 2.0, num_points)
    z = rise * (1.0 - (2.0 * x / span) ** 2)
    y = np.zeros_like(x)

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode="lines",
        line=dict(color="#f39c12", width=8),
        name="Curved Beam",
    ))
    fig.add_trace(go.Scatter3d(
        x=[-span / 2.0, span / 2.0],
        y=[0, 0],
        z=[0, 0],
        mode="markers",
        marker=dict(size=6, color="#2ecc71"),
        name="Supports",
    ))
    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            bgcolor="#0a0e17",
            xaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            yaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            zaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            aspectmode="data",
        ),
        paper_bgcolor="#0a0e17",
        font=dict(color="#e6edf3"),
        margin=dict(l=0, r=0, t=20, b=0),
        height=460,
    )
    return fig


def generate_saddle_span(A, B, rise=2.5, num_points=40):
    """
    Plotly Figure — saddle span (hypar) surface.
    """
    u = np.linspace(-A / 2.0, A / 2.0, num_points)
    v = np.linspace(-B / 2.0, B / 2.0, num_points)
    U, V = np.meshgrid(u, v)
    Z = rise * (U / (A / 2.0)) * (V / (B / 2.0))

    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=U, y=V, z=Z,
        colorscale=[[0, "#111827"], [0.5, "#f39c12"], [1, "#f1c40f"]],
        showscale=False,
        opacity=0.9,
    ))
    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            bgcolor="#0a0e17",
            xaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            yaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            zaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            aspectmode="data",
        ),
        paper_bgcolor="#0a0e17",
        font=dict(color="#e6edf3"),
        margin=dict(l=0, r=0, t=20, b=0),
        height=460,
    )
    return fig


def generate_geodesic_dome_3d(radius=10.0, num_rings=5, num_meridians=12):
    """
    Plotly Figure — geodesic-style dome (hemisphere wireframe).
    radius: sphere radius (m). num_rings: horizontal rings.
    num_meridians: number of meridians.
    """
    fig = go.Figure()

    # Meridians — from pole down to equator
    theta_pole = 0.0
    theta_eq = math.pi / 2.0
    for m in range(num_meridians):
        phi = 2.0 * math.pi * m / num_meridians
        n_pts = 40
        thetas = np.linspace(theta_pole, theta_eq, n_pts)
        xs = radius * np.sin(thetas) * math.cos(phi)
        ys = radius * np.sin(thetas) * math.sin(phi)
        zs = radius * np.cos(thetas)
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color="#f39c12", width=3),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Parallel rings
    for r in range(1, num_rings + 1):
        theta = (math.pi / 2.0) * (r / float(num_rings + 1))
        ring_radius = radius * math.sin(theta)
        z_ring = radius * math.cos(theta)
        phis = np.linspace(0.0, 2.0 * math.pi, 64)
        xs = ring_radius * np.cos(phis)
        ys = ring_radius * np.sin(phis)
        zs = np.full_like(phis, z_ring)
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color="#f1c40f", width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Apex node
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[radius],
        mode="markers",
        marker=dict(size=6, color="#2ecc71"),
        name="Apex",
    ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            bgcolor="#0a0e17",
            xaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            yaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            zaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            aspectmode="data",
        ),
        paper_bgcolor="#0a0e17",
        font=dict(color="#e6edf3"),
        margin=dict(l=0, r=0, t=20, b=0),
        height=460,
    )
    return fig


# ============================== CHUNK 2 END ==================================

# =============================================================================
# UI — TOP NAVIGATION
# =============================================================================

def render_top_nav():
    """Top navigation bar. Sets st.session_state.active_nav on click."""
    nav_items = [
        "Dashboard",
        "Catalog",
        "Workspace",
        "BQ",
        "Reports",
        "Register",
        "Projects",
    ]

    active = st.session_state.get("active_nav", "Dashboard")

    cols = st.columns(len(nav_items))
    for i, item in enumerate(nav_items):
        with cols[i]:
            label = ("● " if item == active else "  ") + item
            if st.button(label, key="nav_" + item, use_container_width=True):
                st.session_state.active_nav = item
                st.rerun()

    st.markdown('<div class="sdse-divider"></div>', unsafe_allow_html=True)


# =============================================================================
# UI — HEADER
# =============================================================================

def render_header():
    """Page header banner."""
    st.markdown(
        """
        <div class="sdse-card" style="background: linear-gradient(90deg, #1a2332 0%, #0a0e17 100%);">
            <h3 style="margin:0;">SDSe — Intelligent Fluid Design Workplace</h3>
            <span class="sdse-badge ec">EN 1990 / 1991 / 1993</span>
            <span class="sdse-badge my">MS EN · Malaysia</span>
            <div class="sdse-muted" style="margin-top:6px;">
                Version 10.0 · Eurocode-aligned structural design for tensile,
                curved-beam and cable structures.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# UI — DASHBOARD
# =============================================================================

def render_dashboard():
    """Dashboard: project info, health score, quick KPIs."""
    render_header()

    st.markdown('<div class="sdse-card"><h3>Project Information</h3>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.project_info["name"] = st.text_input(
            "Project Name",
            value=st.session_state.project_info.get("name", "Untitled Project"),
        )
        st.session_state.project_info["ref"] = st.text_input(
            "Project Ref",
            value=st.session_state.project_info.get("ref", "SDSe-0001"),
        )
    with c2:
        st.session_state.project_info["engineer"] = st.text_input(
            "Engineer",
            value=st.session_state.project_info.get("engineer", ""),
        )
        st.session_state.project_info["client"] = st.text_input(
            "Client",
            value=st.session_state.project_info.get("client", ""),
        )
    with c3:
        st.session_state.project_info["location"] = st.text_input(
            "Location",
            value=st.session_state.project_info.get("location", ""),
        )
        st.session_state.project_info["revision"] = st.text_input(
            "Revision",
            value=st.session_state.project_info.get("revision", "A"),
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sdse-divider"></div>', unsafe_allow_html=True)

    # Health score + KPI row
    health = st.session_state.get("health_score", 0.0)
    results = st.session_state.get("results")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        if health >= 95.0:
            cls = "pass"
        elif health >= 70.0:
            cls = "warn"
        else:
            cls = "fail"
        st.markdown(
            '<div class="sdse-card">'
            '<div class="health-score ' + cls + '">' + str(health) + '</div>'
            '<div class="health-score-label">Health Score</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with c2:
        val = "—"
        if results:
            val = str(results.get("structure_type", "—"))
        st.markdown(
            '<div class="sdse-card">'
            '<div class="sdse-muted">Structure</div>'
            '<div style="font-size:1.05rem;font-weight:600;">' + val + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with c3:
        val = "—"
        if results:
            val = str(results.get("selected_section", "—"))
        st.markdown(
            '<div class="sdse-card">'
            '<div class="sdse-muted">Selected Section</div>'
            '<div style="font-size:1.05rem;font-weight:600;font-family:monospace;">' + val + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with c4:
        val = "—"
        if results:
            val = str(results.get("span_m", "—")) + " m"
        st.markdown(
            '<div class="sdse-card">'
            '<div class="sdse-muted">Span</div>'
            '<div style="font-size:1.05rem;font-weight:600;">' + val + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Check summary if results exist
    if results:
        st.markdown('<div class="sdse-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sdse-card"><h3>Design Checks</h3>', unsafe_allow_html=True)
        checks = results.get("checks", {})
        for key in ["bending", "buckling", "tension", "shear", "deflection"]:
            chk = checks.get(key, {})
            ratio = chk.get("ratio", 0.0)
            status = chk.get("status", "fail")
            st.markdown(
                '<div class="safety-box ' + status + '">'
                '<span>' + key.capitalize() + '</span>'
                '<span class="ratio ' + status + '">'
                + ("%.3f" % ratio) + ' (' + status + ')'
                '</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No design results yet. Go to Workspace to run a design.")


# =============================================================================
# UI — CATALOG
# =============================================================================

def render_catalog():
    """Section catalogue browser."""
    render_header()
    st.markdown('<div class="sdse-card"><h3>Section Catalogue</h3>', unsafe_allow_html=True)

    types = sorted(set(v.get("type", "") for v in SECTION_PROPERTIES.values()))
    type_filter = st.selectbox("Filter by type", ["All"] + types, index=0)

    rows = []
    for name, props in SECTION_PROPERTIES.items():
        if type_filter != "All" and props.get("type") != type_filter:
            continue
        rows.append({
            "Name": name,
            "Type": props.get("type", ""),
            "A (mm²)": props.get("A", 0),
            "I (mm⁴)": props.get("I", 0),
            "W_el (mm³)": props.get("W_el", 0),
            "i (mm)": props.get("i", 0),
            "Weight (kg/m)": props.get("weight", 0),
            "Depth (mm)": props.get("depth", 0),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, height=520)
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# UI — WORKSPACE
# =============================================================================

def render_workspace():
    """Main design workspace: inputs, run button, 3D view, checks, selection."""
    render_header()

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown('<div class="sdse-card"><h3>Structure</h3>', unsafe_allow_html=True)

        structure_type = st.selectbox(
            "Type",
            list(STRUCTURE_TYPES.keys()),
            index=0,
            key="ws_structure_type",
        )
        stype = STRUCTURE_TYPES[structure_type]

        st.markdown('<div class="sdse-muted">Load paths:</div>', unsafe_allow_html=True)
        for lp in stype["load_paths"]:
            st.markdown(
                '<div class="path-card">'
                '<div class="label">Load path</div>'
                '<div class="value">' + lp + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sdse-card"><h3>Geometry (m)</h3>', unsafe_allow_html=True)
        A = st.number_input("A — primary dimension",
                            value=float(st.session_state.params.get("A", stype["default_A"])),
                            min_value=1.0, step=0.5, key="ws_A")
        B = st.number_input("B — secondary dimension",
                            value=float(st.session_state.params.get("B", stype["default_B"])),
                            min_value=1.0, step=0.5, key="ws_B")
        LAA = st.number_input("LAA — length along arc",
                              value=float(st.session_state.params.get("LAA", stype["default_LAA"])),
                              min_value=0.0, step=0.5, key="ws_LAA")

        st.session_state.params["A"] = A
        st.session_state.params["B"] = B
        st.session_state.params["LAA"] = LAA
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sdse-card"><h3>Materials & Standard</h3>', unsafe_allow_html=True)
        standard = st.selectbox(
            "Standard",
            list(WIND_SPEEDS.keys()),
            index=list(WIND_SPEEDS.keys()).index(
                st.session_state.materials.get("standard", "MY")
            ),
            key="ws_standard",
        )
        section_type = st.selectbox(
            "Section family",
            ["CHS", "SHS", "RHS", "I-Beam", "Angle", "Channel"],
            index=["CHS", "SHS", "RHS", "I-Beam", "Angle", "Channel"].index(
                st.session_state.materials.get("section_type", "CHS")
            ),
            key="ws_section_type",
        )
        member_type = st.selectbox(
            "Member type",
            ["Primary", "Secondary", "Bracing"],
            key="ws_member_type",
        )
        joint_type = st.selectbox(
            "Joint type",
            ["Welded", "Bolted", "Pinned"],
            key="ws_joint_type",
        )
        cable_type = st.selectbox(
            "Cable type",
            list(CABLE_PROPERTIES.keys()),
            key="ws_cable_type",
        )
        fabric_type = st.selectbox(
            "Fabric type",
            list(FABRIC_PROPERTIES.keys()),
            key="ws_fabric_type",
        )
        num_bays = st.number_input(
            "Number of bays",
            value=int(st.session_state.materials.get("num_bays", 1)),
            min_value=1, max_value=20, step=1, key="ws_num_bays",
        )

        st.session_state.materials["standard"] = standard
        st.session_state.materials["section_type"] = section_type
        st.session_state.materials["member_type"] = member_type
        st.session_state.materials["joint_type"] = joint_type
        st.session_state.materials["cable_type"] = cable_type
        st.session_state.materials["fabric_type"] = fabric_type
        st.session_state.materials["num_bays"] = int(num_bays)
        st.markdown('</div>', unsafe_allow_html=True)

        run = st.button("⚙ Run Design", use_container_width=True, type="primary")

    with col_right:
        if run:
            with st.spinner("Running Eurocode-aligned design..."):
                results = auto_design_structure(
                    st.session_state.params,
                    st.session_state.materials,
                    structure_type,
                )
            st.session_state.results = results
            st.session_state.health_score = results.get("health", 0.0)
            st.session_state.selected_section = results.get("selected_section")
            st.session_state.bq_rows = generate_bill_of_quantities(
                results, st.session_state.materials
            )

        results = st.session_state.get("results")
        if not results:
            st.info("Press **Run Design** to compute loads, actions, and select a section.")
            return

        # 3D view
        st.markdown('<div class="sdse-card"><h3>3D View</h3>', unsafe_allow_html=True)
        span = results.get("span_m", 10.0)
        if structure_type == "Saddle Span":
            fig = generate_saddle_span(A, B, rise=max(A, B) * 0.10)
        elif structure_type in ("Single Cone Membrane Roof", "Multiple Cone Membrane Roof"):
            fig = generate_geodesic_dome_3d(radius=span / 2.0)
        else:
            fig = generate_curved_beam_3d(span, rise=span * 0.10)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Recommendation
        st.markdown(
            '<div class="member-recommend">'
            '<div class="title">Recommended Section</div>'
            '<div class="spec">' + str(results.get("selected_section", "—")) + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Actions + wind
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("N_Ed", "%.1f kN" % results["actions"]["N_Ed_kN"])
        with c2:
            st.metric("M_Ed", "%.2f kNm" % results["actions"]["M_Ed_kNm"])
        with c3:
            st.metric("V_Ed", "%.1f kN" % results["actions"]["V_Ed_kN"])

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("q_p", "%.3f kPa" % results["wind"]["q_p_kpa"])
        with c2:
            st.metric("Uplift", "%.3f kPa" % results["wind"]["uplift_kpa"])
        with c3:
            st.metric("Pressure", "%.3f kPa" % results["wind"]["pressure_kpa"])

        # Checks
        st.markdown('<div class="sdse-card"><h3>Unity Checks</h3>', unsafe_allow_html=True)
        for key in ["bending", "buckling", "tension", "shear", "deflection"]:
            chk = results["checks"].get(key, {})
            ratio = chk.get("ratio", 0.0)
            status = chk.get("status", "fail")
            st.markdown(
                '<div class="safety-box ' + status + '">'
                '<span>' + key.capitalize() + '</span>'
                '<span class="ratio ' + status + '">'
                + ("%.3f" % ratio) + '</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Selection report
        with st.expander("Section selection report (all candidates)"):
            df = pd.DataFrame(results.get("selection_report", []))
            if not df.empty:
                st.dataframe(df, use_container_width=True)


# =============================================================================
# UI — BILL OF QUANTITIES
# =============================================================================

def render_bq_page():
    """Bill of quantities page."""
    render_header()
    st.markdown('<div class="sdse-card"><h3>Bill of Quantities</h3>', unsafe_allow_html=True)

    rows = st.session_state.get("bq_rows", [])
    if not rows:
        st.info("No BQ yet. Run a design in Workspace first.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    df = pd.DataFrame(rows)
    df["amount"] = df["amount"].astype(float)
    total = df["amount"].sum()

    st.dataframe(df, use_container_width=True)
    st.markdown(
        '<div class="sdse-card">'
        '<div class="sdse-muted">Total estimated cost</div>'
        '<div style="font-size:1.4rem;font-weight:700;color:#f39c12;">'
        'MYR ' + ("{:,.2f}".format(total))
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# UI — REPORTS
# =============================================================================

def render_reports():
    """Design report summary."""
    render_header()
    st.markdown('<div class="sdse-card"><h3>Design Report</h3>', unsafe_allow_html=True)

    results = st.session_state.get("results")
    if not results:
        st.info("No design results available. Run a design in Workspace first.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    info = st.session_state.project_info
    st.markdown(
        '<div class="sdse-muted">Project</div>'
        '<div style="font-weight:600;">' + str(info.get("name", "")) + ' — '
        + str(info.get("ref", "")) + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sdse-divider"></div>', unsafe_allow_html=True)

    st.markdown("**Structure** — " + str(results.get("structure_type", "")))
    st.markdown("**Family** — " + str(results.get("family", "")))
    st.markdown("**Span** — " + ("%.2f m" % results.get("span_m", 0.0)))
    st.markdown("**Plan area** — " + ("%.2f m²" % results.get("plan_area_m2", 0.0)))
    st.markdown("**Selected section** — `" + str(results.get("selected_section", "")) + "`")

    st.markdown('<div class="sdse-divider"></div>', unsafe_allow_html=True)

    health = results.get("health", 0.0)
    status = results.get("health_status", "fail")
    st.markdown(
        '<div class="sdse-card">'
        '<div class="sdse-muted">Health score</div>'
        '<div class="health-score ' + status + '">' + str(health) + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Export JSON
    export = {
        "project": info,
        "params": st.session_state.params,
        "materials": st.session_state.materials,
        "results_summary": {
            "structure_type": results.get("structure_type"),
            "family": results.get("family"),
            "span_m": results.get("span_m"),
            "plan_area_m2": results.get("plan_area_m2"),
            "selected_section": results.get("selected_section"),
            "health": health,
            "health_status": status,
            "actions": results.get("actions"),
            "wind": results.get("wind"),
        },
    }
    st.download_button(
        "⬇ Download report (JSON)",
        data=json.dumps(export, indent=2),
        file_name=str(info.get("ref", "SDSe")) + "_report.json",
        mime="application/json",
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# UI — REGISTRATION
# =============================================================================

def render_registration():
    """Register the current project into st.session_state.registered_projects."""
    render_header()
    st.markdown('<div class="sdse-card"><h3>Register Project</h3>', unsafe_allow_html=True)

    with st.form("register_form"):
        name = st.text_input("Project name",
                             value=st.session_state.project_info.get("name", ""))
        ref = st.text_input("Reference",
                            value=st.session_state.project_info.get("ref", ""))
        engineer = st.text_input("Engineer",
                                 value=st.session_state.project_info.get("engineer", ""))
        submitted = st.form_submit_button("Register")

    if submitted:
        st.session_state.registered_projects.append({
            "name": name,
            "ref": ref,
            "engineer": engineer,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        st.success("Project registered: " + name + " (" + ref + ")")

    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# UI — PROJECT BROWSER
# =============================================================================

def render_project_browser():
    """Browse registered projects."""
    render_header()
    st.markdown('<div class="sdse-card"><h3>Registered Projects</h3>', unsafe_allow_html=True)

    projects = st.session_state.get("registered_projects", [])
    if not projects:
        st.info("No projects registered yet. Go to Register to add one.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    df = pd.DataFrame(projects)
    st.dataframe(df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ============================== CHUNK 3 END ==================================


# =============================================================================
# MAIN — SIDEBAR
# =============================================================================

def render_sidebar_meta():
    """Left sidebar: project quick-info + reset button."""
    with st.sidebar:
        proj_name = str(st.session_state.project_info.get("name", "Untitled"))
        proj_ref = str(st.session_state.project_info.get("ref", ""))
        health_val = str(st.session_state.get("health_score", 0.0))

        sidebar_card = (
            '<div class="sdse-card">'
            + '<h3>' + proj_name + '</h3>'
            + '<div class="sdse-muted">' + proj_ref + '</div>'
            + '</div>'
        )
        st.markdown(sidebar_card, unsafe_allow_html=True)

        health_card = (
            '<div class="sdse-card">'
            + '<div class="sdse-muted">Health</div>'
            + '<div style="font-size:1.6rem;font-weight:700;color:#f39c12;">'
            + health_val
            + '</div></div>'
        )
        st.markdown(health_card, unsafe_allow_html=True)

        meta_card = (
            '<div class="sdse-muted">'
            + 'EN 1990 &middot; EN 1991 &middot; EN 1993 / MS EN<br>'
            + 'gamma_G=1.35 &middot; gamma_Q=1.50 &middot; gamma_M0=1.00 '
            + '&middot; gamma_M1=1.00 &middot; gamma_M2=1.20'
            + '</div>'
        )
        st.markdown(meta_card, unsafe_allow_html=True)

        if st.button("Reset session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# =============================================================================
# MAIN — NAVIGATION DISPATCH
# =============================================================================

def main():
    """Top-level app entry. Renders sidebar + top nav, then dispatches."""
    render_sidebar_meta()
    render_top_nav()

    active = st.session_state.get("active_nav", "Dashboard")

    if active == "Dashboard":
        render_dashboard()
    elif active == "Catalog":
        render_catalog()
    elif active == "Workspace":
        render_workspace()
    elif active == "BQ":
        render_bq_page()
    elif active == "Reports":
        render_reports()
    elif active == "Register":
        render_registration()
    elif active == "Projects":
        render_project_browser()
    else:
        render_dashboard()


# Run the app
main()


# ============================== CHUNK 4 END ==================================

