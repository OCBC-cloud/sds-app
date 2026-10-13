# =============================================================================
# SDSe Fluid Design Studio - Main Entry Point
# =============================================================================
# The whole app is now driven by modules:
#   core/theme.py       - styling
#   core/state.py       - session state initialization
#   core/navigation.py  - page router
#   ui/                 - pages (landing, studio, registration, workshop, results)
#   viewers/            - production 3D viewers
#   engine/             - physics engine (in progress)
#   data/               - section, material, structure catalogues
#
# This file's only job is to set up Streamlit, apply the theme,
# initialize session state, and dispatch to the current page.
#
# Tracking:
#   streamlit-analytics2 wraps the page render. Every visit and every
#   widget click is counted and stored in a local log file inside the
#   app container. Open the app with "?analytics=on" at the end of the
#   URL to see the live dashboard.
#
# Updated 2026-10-13:
#   - Added streamlit-analytics2 tracking around render_current_page().
# =============================================================================

import streamlit as st

import streamlit_analytics2 as sa2

from core.theme import apply_theme
from core.state import init_session_state
from core.navigation import render_current_page


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="SDSe Fluid Design Studio",
    page_icon="⛺",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# BOOTSTRAP
# =============================================================================

apply_theme()
init_session_state()


# =============================================================================
# RENDER (with tracking)
# =============================================================================
# The track() context manager records page views and widget events.
# It does not store IP addresses. Visitor hashes change every day.
# Nothing typed into a text field is stored. No cookies are used.

with sa2.track():
    render_current_page()
