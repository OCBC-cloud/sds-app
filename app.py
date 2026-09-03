import streamlit as st
import json
import os
import plotly.graph_objects as go
import numpy as np

# ============================================================
# PAGE CONFIG (Mobile-Friendly)
# ============================================================
st.set_page_config(
    page_title="SDS Design Studio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit's default menu/footer for a clean app
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ============================================================
# TYPOLOGY CONFIGURATIONS (Built-in)
# ============================================================
TYPOLOGIES = {
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "🏕️",
        "params": {
            "A": {"label": "Rise (m)", "min": 2.0, "max": 20.0, "step": 0.5, "default": 6.0},
            "B": {"label": "Span (m)", "min": 4.0, "max": 40.0, "step": 0.5, "default": 10.0},
            "LAA": {"label": "Apex Distance (m)", "min": 4.0, "max": 50.0, "step": 0.5, "default": 15.0},
            "H": {"label": "Exp. Rise (m)", "min": 2.0, "max": 20.0, "step": 0.5, "default": 6.0}
        },
        "qa": [
            "Two primary curved beams?",
            "Supported at lower ends?",
            "Membrane continuous along beams?",
            "P_A is the apex?",
            "A is vertical rise?",
            "B is horizontal span?",
            "LAA is apex-to-apex distance?"
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
            "Sidewalls open or enclosed?",
            "Ridge height from ground?",
            "Uniform bay distances?",
            "Span measured between outer legs?"
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
            "Edge cables included?",
            "Prestress applied?",
            "Cables anchored to ground?",
            "Fabric type: PVC or PTFE?"
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
            "num_bays": {"label": "Number of Bays", "min": 2, "max": 30, "step": 1, "default": 5},
            "crane_load": {"label": "Crane Load (tonnes)", "min": 0.0, "max": 50.0, "step": 0.5, "default": 0.0}
        },
        "qa": [
            "Column bases pin-supported?",
            "Roof purlin-supported?",
            "Overhead crane (yes/no)?",
            "Fully enclosed cladding?",
            "Wind bracing in walls?",
            "Roof material type?",
            "Crane loads considered?"
        ]
    }
}

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "typology" not in st.session_state:
    st.session_state.typology = None
if "params" not in st.session_state:
    st.session_state.params = {}
if "mode" not in st.session_state:
    st.session_state.mode = "design"  # "design" or "engineer"
if "qa_answers" not in st.session_state:
    st.session_state.qa_answers = {}
if "locked" not in st.session_state:
    st.session_state.locked = False

# ============================================================
# CACHE HANDLER (Silent Auto-Save)
# ============================================================
CACHE_DIR = ".sds_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "current_session.json")

def save_cache():
    data = {
        "typology": st.session_state.typology,
        "params": st.session_state.params,
        "qa_answers": st.session_state.qa_answers,
        "locked": st.session_state.locked
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

# Auto-load cache on boot
cached = load_cache()
if cached:
    st.session_state.typology = cached.get("typology")
    st.session_state.params = cached.get("params", {})
    st.session_state.qa_answers = cached.get("qa_answers", {})
    st.session_state.locked = cached.get("locked", False)

# ============================================================
# 3D GEOMETRY GENERATORS (Simplified for Mobile)
# ============================================================
def generate_saddle_span(params):
    A = params.get("A", 6.0)
    B = params.get("B", 10.0)
    LAA = params.get("LAA", 15.0)
    # Simple parabolic arches
    x = np.linspace(-B/2, B/2, 30)
    y1 = A * (1 - (x/(B/2))**2)
    y2 = A * (1 - (x/(B/2))**2)  # second beam offset by LAA
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=y1, mode='lines', name='Beam 1', line=dict(width=6)))
    fig.add_trace(go.Scatter3d(x=x, y=[LAA]*len(x), z=y2, mode='lines', name='Beam 2', line=dict(width=6)))
    # Membrane (simplified mesh)
    Y, X = np.meshgrid(np.linspace(0, LAA, 10), x)
    Z = A * (1 - (X/(B/2))**2) * (1 - (Y/LAA)**2 * 0.5)  # saddle shape
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.4, colorscale='Blues', showscale=False))
    fig.update_layout(scene=dict(xaxis_title='Span', yaxis_title='Width', zaxis_title='Height'), margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_tent(params):
    span = params.get("span_width", 10.0)
    ridge = params.get("ridge_height", 5.0)
    bays = params.get("num_bays", 4)
    bay_dist = params.get("bay_distance", 5.0)
    total_len = bays * bay_dist
    x = np.linspace(-span/2, span/2, 20)
    z = ridge * (1 - (x/(span/2))**2)
    y = np.linspace(0, total_len, 20)
    fig = go.Figure()
    # Ridge line
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,total_len], z=[ridge,ridge], mode='lines', name='Ridge', line=dict(width=6, color='red')))
    # Eave lines
    fig.add_trace(go.Scatter3d(x=[-span/2,-span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Left', line=dict(width=4)))
    fig.add_trace(go.Scatter3d(x=[span/2,span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Right', line=dict(width=4)))
    # Fabric surface
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), x)
    Z = ridge * (1 - (X/(span/2))**2) * (1 - (Y/total_len)**2 * 0.1)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.5, colorscale='Reds', showscale=False))
    fig.update_layout(scene=dict(xaxis_title='Width', yaxis_title='Length', zaxis_title='Height'), margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_tensile(params):
    mast = params.get("mast_height", 8.0)
    length = params.get("span_length", 20.0)
    width = params.get("span_width", 15.0)
    cables = params.get("cable_count", 4)
    fig = go.Figure()
    # Mast
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0,mast], mode='lines', name='Mast', line=dict(width=8, color='black')))
    # Membrane surface (tent-like)
    X = np.linspace(-length/2, length/2, 20)
    Y = np.linspace(-width/2, width/2, 20)
    X, Y = np.meshgrid(X, Y)
    Z = mast * np.exp(-((X/(length/2))**2 + (Y/(width/2))**2) * 0.5)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.4, colorscale='Greens', showscale=False))
    # Cable lines (simplified)
    for i in range(cables):
        angle = i * 2*np.pi/cables
        x_end = length/2 * np.cos(angle)
        y_end = width/2 * np.sin(angle)
        fig.add_trace(go.Scatter3d(x=[0, x_end], y=[0, y_end], z=[mast, 0], mode='lines', line=dict(width=3, color='gray')))
    fig.update_layout(scene=dict(xaxis_title='Length', yaxis_title='Width', zaxis_title='Height'), margin=dict(l=0,r=0,b=0,t=0))
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
    # One portal frame at y=0
    x = [-span/2, -span/2, 0, span/2, span/2]
    z = [0, eave, ridge, eave, 0]
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', name='Portal Frame', line=dict(width=6, color='blue')))
    # Repeat for multiple bays (simplified)
    for i in range(bays):
        y = i * bay_spacing
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(width=3, color='blue', opacity=0.3)))
    # Roof sheeting surface
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 20))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.3, colorscale='Greys', showscale=False))
    fig.update_layout(scene=dict(xaxis_title='Width', yaxis_title='Length', zaxis_title='Height'), margin=dict(l=0,r=0,b=0,t=0))
    return fig

GENERATORS = {
    "saddle_span": generate_saddle_span,
    "clear_span_tent": generate_tent,
    "tensile_membrane": generate_tensile,
    "portal_frame": generate_portal
}

# ============================================================
# UI RENDERING
# ============================================================
st.title("🏗️ SDS Design Studio")

# ---- CATALOG VIEW (If no typology selected) ----
if st.session_state.typology is None:
    st.subheader("Choose a structure type:")
    cols = st.columns(2)
    idx = 0
    for key, typ in TYPOLOGIES.items():
        with cols[idx % 2]:
            if st.button(f"{typ['icon']} {typ['name']}", use_container_width=True):
                st.session_state.typology = key
                # Load default params
                st.session_state.params = {p: v["default"] for p, v in typ["params"].items()}
                st.session_state.qa_answers = {}
                st.session_state.locked = False
                save_cache()
                st.rerun()
        idx += 1
    st.stop()

# ---- ACTIVE TYPOLOGY VIEW ----
typ_key = st.session_state.typology
typ = TYPOLOGIES[typ_key]
params = st.session_state.params

# Header with back button
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("⬅", help="Back to catalog"):
        st.session_state.typology = None
        st.session_state.mode = "design"
        st.session_state.locked = False
        save_cache()
        st.rerun()
with col2:
    st.subheader(f"{typ['icon']} {typ['name']}")
with col3:
    # Mode Toggle Button (Design ↔ Engineer)
    if st.session_state.mode == "design":
        if st.button("🔍 Pro View", use_container_width=True):
            st.session_state.mode = "engineer"
            save_cache()
            st.rerun()
    else:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.mode = "design"
            save_cache()
            st.rerun()

# ---- LOCK STATUS ----
if st.session_state.locked:
    st.warning("🔒 Design is LOCKED. Edit mode is disabled.")

# ---- DESIGN MODE: Sliders + Q&A ----
if st.session_state.mode == "design" and not st.session_state.locked:
    # Parameters
    st.subheader("📐 Dimensions")
    cols = st.columns(2)
    col_idx = 0
    for p_key, p_def in typ["params"].items():
        with cols[col_idx % 2]:
            val = st.slider(
                p_def["label"],
                min_value=float(p_def["min"]),
                max_value=float(p_def["max"]),
                step=float(p_def["step"]),
                value=float(params.get(p_key, p_def["default"]))
            )
            params[p_key] = val
        col_idx += 1
    
    # Auto-save on slider change (debounced via session state)
    save_cache()
    
    # Q&A Board
    st.subheader("📋 Confirm Design")
    for i, q in enumerate(typ["qa"]):
        key = f"qa_{i}"
        default = st.session_state.qa_answers.get(key, "Yes")
        options = ["Yes", "No", "Not Sure"] if "?" in q else ["Open", "Enclosed", "PVC", "PTFE", "Steel"]
        if "?" in q:
            ans = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes","No","Not Sure"].index(default), key=key)
        else:
            ans = st.selectbox(q, options, index=options.index(default) if default in options else 0, key=key)
        st.session_state.qa_answers[key] = ans
    save_cache()
    
    # Lock Button
    if st.button("🔒 LOCK & PROCEED", use_container_width=True, type="primary"):
        st.session_state.locked = True
        save_cache()
        st.rerun()

# ---- ENGINEER MODE OR LOCKED: High-Res View + Overlays ----
if st.session_state.mode == "engineer" or st.session_state.locked:
    st.subheader("🔬 Structural View")
    
    # Generate 3D Plot
    if typ_key in GENERATORS:
        fig = GENERATORS[typ_key](params)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Show Q&A answers as summary
    with st.expander("📋 Design Summary (Locked)"):
        for i, q in enumerate(typ["qa"]):
            ans = st.session_state.qa_answers.get(f"qa_{i}", "Not answered")
            st.write(f"**{q}** → {ans}")
    
    # If locked, show unlock option
    if st.session_state.locked:
        if st.button("🔓 Unlock to Edit", use_container_width=True):
            st.session_state.locked = False
            st.session_state.mode = "design"
            save_cache()
            st.rerun()

# ---- FOOTER ----
st.caption("SDS Platform v1.0 | Built for mobile | Cache auto-saves all changes.")

# ============================================================
# RUN: Save cache on every interaction
# ============================================================
save_cache()
