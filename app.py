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
# =============================================================================

import streamlit as st

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
render_current_page()
