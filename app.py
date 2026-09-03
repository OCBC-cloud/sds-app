import streamlit as st
import json
import os
import plotly.graph_objects as go
import numpy as np
from PIL import Image
import io
import base64

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
    },
    "custom": {
        "name": "Custom Design",
        "icon": "🧩",
        "params": {
            "width": {"label": "Overall Width (m)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 10.0},
            "length": {"label": "Overall Length (m)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 15.0},
            "height": {"label": "Overall Height (m)", "min": 1.0, "max": 50.0, "step": 0.5, "default": 8.0}
        },
        "qa": [
            "This is a custom design. Add your description below."
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
    st.session_state.mode = "design"
if "qa_answers" not in st.session_state:
    st.session_state.qa_answers = {}
if "locked" not in st.session_state:
    st.session_state.locked = False
if "custom_image" not in st.session_state:
    st.session_state.custom_image = None
if "custom_description" not in st.session_state:
    st.session_state.custom_description = ""

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
        "locked": st.session_state.locked,
        "custom_image": st.session_state.custom_image,
        "custom_description": st.session_state.custom_description
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
    st.session_state.custom_image = cached.get("custom_image")
    st.session_state.custom_description = cached.get("custom_description", "")

# ============================================================
# 3D GEOMETRY GENERATORS
# ============================================================

# -------- CORRECTED SADDLE SPAN --------
def generate_saddle_span(params):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    num_points = 40

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    x = np.linspace(-span/2, span/2, num_points)
    z_beam = rise * (1 - (2 * x / span)**2)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    u = np.linspace(0, 1, num_points)
    v = np.linspace(0, 1, num_points)

    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, u_val in enumerate(u):
        x_pos = -span/2 + u_val * span
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = rise * (1 - (2 * x_pos / span)**2) if abs(x_pos) <= span/2 else 0

        for j, v_val in enumerate(v):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            saddle_factor = 1 - 0.3 * (1 - (2 * v_val - 1)**2)
            z_pos = z_at_x * saddle_factor
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=6)))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=6)))
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, colorscale=[[0, '#E8E8E8'], [1, '#F5F5F5']], opacity=0.8, showscale=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[rise], mode='markers', name='Apex 1', marker=dict(color='#FFD93D', size=10)))
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[rise], mode='markers', name='Apex 2', marker=dict(color='#FFD93D', size=10)))
    fig.add_trace(go.Scatter3d(x=[-span/2], y=[0], z=[0], mode='markers', name='Support 1', marker=dict(color='#4ECDC4', size=10)))
    fig.add_trace(go.Scatter3d(x=[span/2], y=[0], z=[0], mode='markers', name='Support 2', marker=dict(color='#4ECDC4', size=10)))
    fig.update_layout(scene=dict(xaxis_title='Span (m)', yaxis_title='Width (m)', zaxis_title='Height (m)'), margin=dict(l=0,r=0,b=0,t=0))
    return fig

# -------- SIMPLIFIED GENERATORS FOR OTHER TYPOLOGIES --------
def generate_tent(params):
    span = params.get("span_width", 10.0)
    ridge = params.get("ridge_height", 5.0)
    bays = params.get("num_bays", 4)
    bay_dist = params.get("bay_distance", 5.0)
    total_len = bays * bay_dist
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,total_len], z=[ridge,ridge], mode='lines', name='Ridge', line=dict(width=6, color='red')))
    fig.add_trace(go.Scatter3d(x=[-span/2,-span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Left', line=dict(width=4)))
    fig.add_trace(go.Scatter3d(x=[span/2,span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Right', line=dict(width=4)))
    X = np.linspace(-span/2, span/2, 20)
    Y = np.linspace(0, total_len, 20)
    X, Y = np.meshgrid(X, Y)
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
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0,mast], mode='lines', name='Mast', line=dict(width=8, color='black')))
    X = np.linspace(-length/2, length/2, 20)
    Y = np.linspace(-width/2, width/2, 20)
    X, Y = np.meshgrid(X, Y)
    Z = mast * np.exp(-((X/(length/2))**2 + (Y/(width/2))**2) * 0.5)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.4, colorscale='Greens', showscale=False))
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
    x = [-span/2, -span/2, 0, span/2, span/2]
    z = [0, eave, ridge, eave, 0]
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', name='Portal Frame', line=dict(width=6, color='blue')))
    for i in range(bays):
        y = i * bay_spacing
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(width=3, color='blue', opacity=0.3)))
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 20))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.3, colorscale='Greys', showscale=False))
    fig.update_layout(scene=dict(xaxis_title='Width', yaxis_title='Length', zaxis_title='Height'), margin=dict(l=0,r=0,b=0,t=0))
    return fig

# -------- CUSTOM: Bounding Box + Design Brief --------
def generate_custom_bounding_box(params):
    width = params.get("width", 10.0)
    length = params.get("length", 15.0)
    height = params.get("height", 8.0)
    
    fig = go.Figure()
    
    # Bounding box wireframe
    # 8 corners of the box
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
    
    # Edges (connect corners)
    edges = [
        (0,1), (1,2), (2,3), (3,0),  # bottom
        (4,5), (5,6), (6,7), (7,4),  # top
        (0,4), (1,5), (2,6), (3,7)   # vertical
    ]
    
    # Draw each edge as a line
    for i, j in edges:
        fig.add_trace(go.Scatter3d(
            x=[corners[i][0], corners[j][0]],
            y=[corners[i][1], corners[j][1]],
            z=[corners[i][2], corners[j][2]],
            mode='lines',
            line=dict(color='#00B4D8', width=3),
            showlegend=False
        ))
    
    # Add transparent faces (optional)
    # Just show the wireframe for now
    
    # Add dimension labels
    fig.add_trace(go.Scatter3d(
        x=[0], y=[-length/2 - 1], z=[height/2],
        mode='text',
        text=[f"W: {width:.1f}m"],
        textfont=dict(color='#FFD93D', size=12),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[width/2 + 1], y=[0], z=[height/2],
        mode='text',
        text=[f"L: {length:.1f}m"],
        textfont=dict(color='#4ECDC4', size=12),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[width/2 + 0.5], y=[-length/2 - 0.5], z=[height/2],
        mode='text',
        text=[f"H: {height:.1f}m"],
        textfont=dict(color='#FF6B6B', size=12),
        showlegend=False
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)',
            yaxis_title='Length (m)',
            zaxis_title='Height (m)',
            aspectmode='manual',
            aspectratio=dict(x=1.5, y=2.0, z=0.8)
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor='rgba(0,0,0,0)',
        scene_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def generate_custom_with_image(params, image_data):
    """Generate a 3D view with image overlay if available."""
    fig = generate_custom_bounding_box(params)
    
    # If image exists, we could overlay it as a texture
    # For simplicity, we just display the bounding box with a note
    
    return fig

GENERATORS = {
    "saddle_span": generate_saddle_span,
    "clear_span_tent": generate_tent,
    "tensile_membrane": generate_tensile,
    "portal_frame": generate_portal,
    "custom": generate_custom_bounding_box
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

if st.session_state.locked:
    st.warning("🔒 Design is LOCKED. Edit mode is disabled.")

# ---- CUSTOM TYPOLOGY: Image Upload + Description ----
if typ_key == "custom":
    st.subheader("📋 Design Brief")
    
    # Image Upload
    uploaded_file = st.file_uploader(
        "Upload sketch or photo (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        help="Upload a sketch, photo, or reference image for your custom design."
    )
    
    if uploaded_file:
        # Save image to session state
        st.session_state.custom_image = uploaded_file.getvalue()
        st.image(uploaded_file, caption="Design Reference", use_column_width=True)
    
    # Description
    description = st.text_area(
        "Describe your design:",
        value=st.session_state.custom_description,
        placeholder="e.g., Three curved steel beams meeting at a central ring, supported by 6 cables anchored to the ground.",
        height=100
    )
    st.session_state.custom_description = description
    
    # Parameters (sliders)
    st.subheader("📐 Bounding Box Dimensions")
    cols = st.columns(3)
    with cols[0]:
        width = st.slider(
            "Width (m)",
            min_value=1.0, max_value=100.0, step=0.5,
            value=params.get("width", 10.0)
        )
        params["width"] = width
    with cols[1]:
        length = st.slider(
            "Length (m)",
            min_value=1.0, max_value=100.0, step=0.5,
            value=params.get("length", 15.0)
        )
        params["length"] = length
    with cols[2]:
        height = st.slider(
            "Height (m)",
            min_value=1.0, max_value=50.0, step=0.5,
            value=params.get("height", 8.0)
        )
        params["height"] = height
    
    # Q&A for custom (just a note)
    st.info("📝 This is a custom design. The 3D view shows a bounding box placeholder. Your design brief (image + description) is saved in the cache.")
    
    # Lock button
    if st.button("🔒 LOCK DESIGN BRIEF", use_container_width=True, type="primary"):
        st.session_state.locked = True
        save_cache()
        st.rerun()

# ---- REGULAR TYPOLOGIES: Sliders + Q&A ----
else:
    if st.session_state.mode == "design" and not st.session_state.locked:
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
        
        save_cache()
        
        st.subheader("📋 Confirm Design")
        for i, q in enumerate(typ["qa"]):
            key = f"qa_{i}"
            default = st.session_state.qa_answers.get(key, "Yes")
            if "?" in q:
                ans = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes","No","Not Sure"].index(default), key=key)
            else:
                options = ["Open", "Enclosed", "PVC", "PTFE", "Steel"]
                ans = st.selectbox(q, options, index=options.index(default) if default in options else 0, key=key)
            st.session_state.qa_answers[key] = ans
        save_cache()
        
        if st.button("🔒 LOCK & PROCEED", use_container_width=True, type="primary"):
            st.session_state.locked = True
            save_cache()
            st.rerun()

# ---- ENGINEER MODE OR LOCKED: 3D View + Summary ----
if st.session_state.mode == "engineer" or st.session_state.locked:
    st.subheader("🔬 3D View")
    
    # For custom, show bounding box with image reference
    if typ_key == "custom":
        fig = generate_custom_bounding_box(params)
        
        # If image exists, show it alongside the 3D view
        if st.session_state.custom_image:
            st.image(st.session_state.custom_image, caption="Design Reference", use_column_width=True)
        
        # Show description
        if st.session_state.custom_description:
            st.caption(f"📝 {st.session_state.custom_description}")
    
    else:
        if typ_key in GENERATORS:
            fig = GENERATORS[typ_key](params)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Summary
    with st.expander("📋 Design Summary"):
        for i, q in enumerate(typ["qa"]):
            ans = st.session_state.qa_answers.get(f"qa_{i}", "Not answered")
            st.write(f"**{q}** → {ans}")
        
        if typ_key == "custom":
            st.write("**📝 Custom Design Brief**")
            st.write(f"Width: {params.get('width', 10.0):.1f}m")
            st.write(f"Length: {params.get('length', 15.0):.1f}m")
            st.write(f"Height: {params.get('height', 8.0):.1f}m")
            if st.session_state.custom_description:
                st.write(f"Description: {st.session_state.custom_description}")
    
    if st.session_state.locked:
        if st.button("🔓 Unlock to Edit", use_container_width=True):
            st.session_state.locked = False
            st.session_state.mode = "design"
            save_cache()
            st.rerun()

# ---- FOOTER ----
st.caption("SDS Platform v1.0 | Built for mobile | Cache auto-saves all changes.")
save_cache()
