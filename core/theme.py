# =============================================================================
# SDSe - Theme and Global CSS
# =============================================================================
# All styling for the app: dark theme, colours, card layouts, buttons,
# inputs, alerts, health score card, and mobile responsiveness.
#
# This version (Phase A, Chunk A0) focuses on READABILITY:
#   - High-contrast text on all widget types
#   - Visible placeholder text in inputs
#   - Clear focus and hover states
#   - Minimum 4.5:1 contrast ratio for body text (WCAG AA)
#   - Bumped font sizes for labels and values
#
# Contents:
#   DARK_MODE_CSS   - the full CSS string injected via st.markdown
#   apply_theme()   - convenience function that injects the CSS
# =============================================================================

import streamlit as st


# =============================================================================
# CSS STRING
# =============================================================================

DARK_MODE_CSS = """
    <style>
    /* =========================================================================
       BASE - App background and text
       ========================================================================= */
    .stApp {
        background-color: #0a0e17 !important;
        color: #f0f4fa !important;
    }
       .stApp > header { display: none !important; }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* =========================================================================
       TYPOGRAPHY - High contrast
       ========================================================================= */
 /*    h1 Labels, on h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    p, span, div { color: #e6edf3; }

 widgets */
    .stApp label,
    .stApp .stSelectbox label,
    .stApp .stNumberInput label,
    .stApp .stTextInput label,
    .stApp .stSlider label,
    .stApp .stRadio label,
    .stApp .stCheckbox label {
        color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }

    /* =========================================================================
       BUTTONS - Clear, high contrast
       ========================================================================= */
    .stApp .stButton > button {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
        border: 1px solid #3a4a5f !important;
        border-radius: 8px !important;
        padding: 0.55rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    .stApp .stButton > button:hover {
        background-color: #2a3a4f !important;
        border-color: #f39c12 !important;
        color: #f39c12 !important;
        transform: translateY(-1px) !important;
    }
    .stApp .stButton > button[kind="primary"] {
        background-color: #f39c12 !important;
        color: #0a0e17 !important;
        border: 1px solid #f39c12 !important;
        font-weight: 700 !important;
    }
    .stApp .stButton > button[kind="primary"]:hover {
        background-color: #f1c40f !important;
        border-color: #f1c40f !important;
        color: #0a0e17 !important;
    }
    .stApp .stButton > button[kind="secondary"] {
        background-color: #2a3a4f !important;
        color: #ffffff !important;
        border: 1px solid #4a7a9c !important;
    }

    /* Download and form submit buttons */
    .stApp .stDownloadButton > button,
    .stApp .stFormSubmitButton > button {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
        border: 1px solid #3a4a5f !important;
        border-radius: 8px !important;
        padding: 0.55rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    .stApp .stDownloadButton > button:hover,
    .stApp .stFormSubmitButton > button:hover {
        background-color: #2a3a4f !important;
        border-color: #f39c12 !important;
        color: #f39c12 !important;
    }

    /* =========================================================================
       TEXT INPUTS - High contrast, visible placeholder
       ========================================================================= */
    .stApp .stTextInput > div > div > input,
    .stApp .stNumberInput > div > div > input {
        background-color: #141e2b !important;
        color: #ffffff !important;
        border: 1px solid #3a4a5f !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        padding: 0.5rem 0.75rem !important;
    }
    .stApp .stTextInput > div > div > input::placeholder,
    .stApp .stNumberInput > div > div > input::placeholder,
    .stApp .stTextArea textarea::placeholder {
        color: #8a9aaa !important;
        opacity: 1 !important;
    }
    .stApp .stTextArea textarea {
        background-color: #141e2b !important;
        color: #ffffff !important;
        border: 1px solid #3a4a5f !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
    }
    .stApp .stTextInput > div > div > input:focus,
    .stApp .stNumberInput > div > div > input:focus,
    .stApp .stTextArea textarea:focus {
        border-color: #f39c12 !important;
        box-shadow: 0 0 0 2px rgba(243, 156, 18, 0.25) !important;
        outline: none !important;
    }

    /* Number input +/- buttons */
    .stApp .stNumberInput > div > div > div > button {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
        border: 1px solid #3a4a5f !important;
    }
    .stApp .stNumberInput > div > div > div > button:hover {
        background-color: #2a3a4f !important;
        color: #f39c12 !important;
        border-color: #f39c12 !important;
    }

    /* =========================================================================
       SELECTBOX - High contrast
       ========================================================================= */
    .stApp .stSelectbox > div > div > div {
        background-color: #141e2b !important;
        color: #ffffff !important;
        border: 1px solid #3a4a5f !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
    }
    .stApp .stSelectbox > div > div > div:hover {
        border-color: #f39c12 !important;
    }
    /* Dropdown menu items */
    .stApp ul[role="listbox"] li,
    .stApp div[role="option"] {
        background-color: #141e2b !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
    }
    .stApp div[role="option"]:hover {
        background-color: #2a3a4f !important;
        color: #f39c12 !important;
    }

    /* =========================================================================
       RADIO BUTTONS - High contrast labels
       ========================================================================= */
    .stApp .stRadio > div {
        gap: 0.6rem !important;
    }
    .stApp .stRadio > div > label {
        color: #ffffff !important;
        background-color: #141e2b !important;
        padding: 0.55rem 1rem !important;
        border-radius: 8px !important;
        border: 1px solid #3a4a5f !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        width: 100% !important;
    }
    .stApp .stRadio > div > label:hover {
        border-color: #f39c12 !important;
        color: #f39c12 !important;
        background-color: #1e2a3a !important;
    }
    /* Selected radio label */
    .stApp .stRadio > div > label[data-checked="true"],
    .stApp .stRadio > div > label[aria-checked="true"] {
        color: #f39c12 !important;
        border-color: #f39c12 !important;
        background-color: rgba(243, 156, 18, 0.1) !important;
        font-weight: 600 !important;
    }

    /* =========================================================================
       CHECKBOXES - High contrast labels
       ========================================================================= */
    .stApp .stCheckbox > label {
        color: #ffffff !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }

    /* =========================================================================
       SLIDER - High contrast
       ========================================================================= */
    .stApp .stSlider > div > div > div {
        background-color: #3a4a5f !important;
    }
    .stApp .stSlider > div > div > div > div {
        background-color: #f39c12 !important;
    }
    .stApp .stSlider > div > div > div > div > div {
        background-color: #f39c12 !important;
        border: 2px solid #0a0e17 !important;
    }
    /* Slider value label */
    .stApp .stSlider [data-testid="stTickBarMin"],
    .stApp .stSlider [data-testid="stTickBarMax"] {
        color: #b0c4de !important;
        font-size: 0.85rem !important;
    }

    /* =========================================================================
       ALERTS
       ========================================================================= */
    .stApp .stAlert {
        background-color: #1e2a3a !important;
        border-left: 4px solid #f39c12 !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        padding: 0.8rem 1rem !important;
    }
    .stApp .stAlert p,
    .stApp .stAlert div,
    .stApp .stAlert span {
        color: #ffffff !important;
    }
    .stApp .stInfo {
        background-color: #1a2a3a !important;
        border-left-color: #4a7a9c !important;
    }
    .stApp .stSuccess {
        background-color: #1a3a2a !important;
        border-left-color: #2ecc71 !important;
    }
    .stApp .stError {
        background-color: #3a1a1a !important;
        border-left-color: #e74c3c !important;
    }
    .stApp .stWarning {
        background-color: #4a3a1a !important;
        border-left-color: #f39c12 !important;
    }

    /* =========================================================================
       HIDE DEFAULT STREAMLIT CHROME
       ========================================================================= */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    /* =========================================================================
       PLOTLY 3D VIEWER CONTAINER
       ========================================================================= */
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

    /* =========================================================================
       CARDS - sdse-card
       ========================================================================= */
    .sdse-card {
        background-color: #121e2e;
        border-radius: 12px;
        padding: 1.2rem;
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

    /* =========================================================================
       DASHBOARD CARDS
       ========================================================================= */
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
    .dash-card .value {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0.3rem 0;
    }
    .dash-card .label {
        color: #a8b8c8;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* =========================================================================
       PATH CARDS (structure type tiles)
       ========================================================================= */
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
    .path-card .title {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    .path-card .desc {
        color: #a8b8c8;
        font-size: 0.85rem;
        margin-top: 0.3rem;
        line-height: 1.4;
    }

    /* =========================================================================
       SAFETY BOX
       ========================================================================= */
    .safety-box {
        background-color: #1a2a3a;
        border-left: 4px solid #f39c12;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .safety-box .highlight {
        color: #f39c12;
        font-weight: 600;
    }

    /* =========================================================================
       HEALTH SCORE
       ========================================================================= */
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
        color: #d0dff0;
        font-size: 0.95rem;
    }

    /* =========================================================================
       RESULT ROWS
       ========================================================================= */
    .result-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #1a2a3a;
        font-size: 0.95rem;
    }
    .result-row .label { color: #a8b8c8; }
    .result-row .value { color: #ffffff; font-weight: 600; }
    .result-row .pass { color: #2ecc71; font-weight: 600; }
    .result-row .check { color: #f39c12; font-weight: 600; }
    .result-row .fail { color: #e74c3c; font-weight: 600; }

    /* =========================================================================
       MEMBER RECOMMENDATION BOX
       ========================================================================= */
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
        color: #a8b8c8;
        font-size: 0.8rem;
    }
    .member-recommend .status-pass {
        color: #2ecc71;
        font-weight: 700;
    }
    .member-recommend .status-check {
        color: #f39c12;
        font-weight: 700;
    }

    /* =========================================================================
       METRIC CARDS (for results)
       ========================================================================= */
    .metric-card {
        background-color: #141e2b;
        border-radius: 12px;
        padding: 0.9rem;
        border: 1px solid #1e2a3a;
        text-align: center;
    }
    .metric-card .value {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 700;
    }
    .metric-card .label {
        color: #a8b8c8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* =========================================================================
       BADGES
       ========================================================================= */
    .sdse-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 5px;
    }
    .sdse-badge.ec {
        background: #f39c1233;
        color: #f39c12;
        border: 1px solid #f39c12;
    }
    .sdse-badge.my {
        background: #2ecc7133;
        color: #2ecc71;
        border: 1px solid #2ecc71;
    }
    .sdse-badge.leaf {
        background: #f39c1233;
        color: #f39c12;
        border: 1px solid #f39c12;
    }
    .sdse-badge.column {
        background: #2ecc7133;
        color: #2ecc71;
        border: 1px solid #2ecc71;
    }
    .sdse-badge.rib {
        background: #3498db33;
        color: #3498db;
        border: 1px solid #3498db;
    }

    /* =========================================================================
       DIVIDER
       ========================================================================= */
    .sdse-divider {
        height: 1px;
        background-color: #2a3441;
        margin: 14px 0;
    }

    /* =========================================================================
       MUTED TEXT
       ========================================================================= */
    .sdse-muted {
        color: #a8b8c8;
        font-size: 0.85rem;
    }

    /* =========================================================================
       RESPONSIVE
       ========================================================================= */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
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
