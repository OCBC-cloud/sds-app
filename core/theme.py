# =============================================================================
# SDSe - Theme and Global CSS
# =============================================================================
# All styling for the app: dark theme, colours, card layouts, buttons,
# inputs, alerts, health score card, and mobile responsiveness.
#
# Contents:
#   DARK_MODE_CSS   - the full CSS string injected via st.markdown
#   apply_theme()   - convenience function that injects the CSS
#
# Usage:
#   from core.theme import apply_theme
#   apply_theme()
# =============================================================================

import streamlit as st


# =============================================================================
# CSS STRING
# =============================================================================

DARK_MODE_CSS = """
    <style>
    /* Reset and Base */
    .stApp { background-color: #0a0e17 !important; color: #f0f4fa !important; }
    .stApp > header { display: none !important; }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 600 !important; }
    label { color: #ffffff !important; font-weight: 400 !important; font-size: 0.85rem !important; }

    /* Buttons */
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

    /* Inputs */
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

    /* Alerts */
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

    /* Hide Elements */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    /* 3D Viewer */
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

    /* Cards */
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

    /* Dashboard Cards */
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

    /* Design Path Cards */
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

    /* Safety Box */
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

    /* Health Score */
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

    /* Results Table */
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

    /* Member Recommendation */
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

    /* Layout Utilities */
    .mt-1 { margin-top: 0.5rem; }
    .mt-2 { margin-top: 1rem; }
    .mb-1 { margin-bottom: 0.5rem; }
    .mb-2 { margin-bottom: 1rem; }
    .flex-between { display: flex; justify-content: space-between; align-items: center; }
    .gap-1 { gap: 0.5rem; }
    .gap-2 { gap: 1rem; }

    /* Responsive */
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


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def apply_theme():
    """Inject the global CSS into the Streamlit app. Call once near the top."""
    st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)
