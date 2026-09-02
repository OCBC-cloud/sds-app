import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import uuid
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import base64
import plotly.graph_objects as go
import time
import json
import zipfile
from io import BytesIO
import numpy as np
import re
import requests

# ============================================================================
# Page Configuration & Session State
# ============================================================================

if 'fullscreen' not in st.session_state:
    st.session_state.fullscreen = False

st.set_page_config(
    page_title="SDS Design Portal",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom Dark Theme CSS
# ============================================================================

st.markdown("""
<style>
    .stApp { background-color: #1E1E1E; }
    .css-1d391kg { background-color: #2A2A2A; }
    .stTextInput label, .stTextArea label, .stNumberInput label, 
    .stSelectbox label, .stDateInput label, .stRadio label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #3A3A3A !important;
        color: #FFFFFF !important;
        border: 1px solid #5A5A5A !important;
        border-radius: 8px !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #A0A0A0 !important;
    }
    .stSelectbox select {
        background-color: #3A3A3A !important;
        color: #FFFFFF !important;
        border: 1px solid #5A5A5A !important;
        border-radius: 8px !important;
    }
    .stButton button {
        background-color: #00B4D8 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .stButton button:hover { background-color: #0090B0 !important; }
    .stButton button[data-testid="baseButton-secondary"] {
        background-color: #4A4A4A !important;
    }
    .stButton button[data-testid="baseButton-secondary"]:hover {
        background-color: #5A5A5A !important;
    }
    h1, h2, h3, h4, .stSubheader { color: #FFFFFF !important; }
    .stCaption, .stMarkdown p, .stText { color: #D0D0D0 !important; }
    .stAlert { background-color: #2A3A2A !important; border-color: #52B788 !important; color: #D4EDDA !important; }
    .stError { background-color: #3A2A2A !important; border-color: #E63946 !important; color: #F8D7DA !important; }
    .stInfo { background-color: #2A3A4A !important; border-color: #00B4D8 !important; color: #D4EDF4 !important; }
    .stWarning { background-color: #4A3A2A !important; border-color: #F4A261 !important; color: #FFF3E0 !important; }
    hr { border-color: #3A3A3A !important; }
    .stProgress > div > div { background-color: #00B4D8 !important; }
    div[data-testid="metric-container"] label { color: #FFFFFF !important; }
    div[data-testid="metric-container"] div { color: #FFFFFF !important; }
    .project-card {
        background-color: #2A2A2A;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        border-left: 4px solid #00B4D8;
    }
    .project-card strong { color: #FFFFFF !important; }
    .project-card span { color: #B0B0B0 !important; }
    .load-options-card {
        background-color: #2A3A4A;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #4A6A7A;
        margin-bottom: 16px;
    }
    .interpretation-card {
        background-color: #2A3A2A;
        padding: 16px;
        border-radius: 8px;
        border-left: 4px solid #52B788;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Supabase Setup
# ============================================================================

SUPABASE_URL = "https://pcijgufnjeijqqywubpu.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# Session State Initialization
# ============================================================================

if 'stage' not in st.session_state:
    st.session_state.stage = 0
if 'project_id' not in st.session_state:
    st.session_state.project_id = None
if 'iteration_id' not in st.session_state:
    st.session_state.iteration_id = None
if 'frozen' not in st.session_state:
    st.session_state.frozen = False
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = '3D'
if 'cached_fig' not in st.session_state:
    st.session_state.cached_fig = None
if 'cached_inputs' not in st.session_state:
    st.session_state.cached_inputs = None
if 'design_parameters' not in st.session_state:
    st.session_state.design_parameters = {}
if 'understanding_locked' not in st.session_state:
    st.session_state.understanding_locked = False
if 'iteration_count' not in st.session_state:
    st.session_state.iteration_count = 0
if 'feedback_history' not in st.session_state:
    st.session_state.feedback_history = []
if 'project_name' not in st.session_state:
    st.session_state.project_name = ''
if 'client_name' not in st.session_state:
    st.session_state.client_name = ''
if 'main_contractor' not in st.session_state:
    st.session_state.main_contractor = ''
if 'contact_phone' not in st.session_state:
    st.session_state.contact_phone = ''
if 'contact_email' not in st.session_state:
    st.session_state.contact_email = ''
if 'project_date' not in st.session_state:
    st.session_state.project_date = datetime.now().date()
if 'load_options' not in st.session_state:
    st.session_state.load_options = None
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []
if 'round' not in st.session_state:
    st.session_state.round = 0
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = ''
if 'interpretation' not in st.session_state:
    st.session_state.interpretation = None
if 'interpretation_source' not in st.session_state:
    st.session_state.interpretation_source = None

# ============================================================================
# Helper Functions
# ============================================================================

def clear_stage_fields(stage):
    keys_to_clear = []
    if stage == 1:
        keys_to_clear = ['proj_name', 'client_name', 'main_contractor', 'contact_phone', 'contact_email', 'project_date']
    elif stage == 2:
        keys_to_clear = ['description', 'uploaded_images', 'interpretation']
    elif stage == 3:
        keys_to_clear = ['stakeholder', 'message']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def load_project(project_id, iteration_id, stage):
    st.session_state.project_id = project_id
    st.session_state.iteration_id = iteration_id
    st.session_state.stage = stage
    try:
        result = supabase.table('projects').select('*').eq('id', project_id).execute()
        if result.data:
            data = result.data[0]
            st.session_state.project_name = data.get('name', '')
            st.session_state.client_name = data.get('client_name', '')
            st.session_state.main_contractor = data.get('main_contractor', '')
            st.session_state.contact_phone = data.get('contact_phone', '')
            st.session_state.contact_email = data.get('contact_email', '')
            st.session_state.project_date = data.get('project_date', datetime.now().date())
            state = data.get('design_state', {})
            if isinstance(state, dict):
                st.session_state.design_parameters = state.get('parameters', {})
                st.session_state.iteration_count = state.get('iteration_count', 0)
                st.session_state.feedback_history = state.get('feedback_history', [])
                st.session_state.frozen = state.get('frozen', False)
                st.session_state.uploaded_images = state.get('uploaded_images', [])
                st.session_state.round = state.get('round', 0)
                st.session_state.interpretation = state.get('interpretation', None)
    except Exception as e:
        pass
    st.rerun()

def delete_project(project_id):
    try:
        supabase.table('projects').delete().eq('id', project_id).execute()
        st.success("✅ Project deleted successfully.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error deleting project: {str(e)}")

def save_design_state(project_id):
    state = {
        'parameters': st.session_state.design_parameters,
        'iteration_count': st.session_state.iteration_count,
        'feedback_history': st.session_state.feedback_history,
        'frozen': st.session_state.frozen,
        'uploaded_images': st.session_state.uploaded_images,
        'round': st.session_state.round,
        'interpretation': st.session_state.interpretation,
        'last_modified': datetime.now().isoformat()
    }
    try:
        supabase.table('projects').update({'design_state': state}).eq('id', project_id).execute()
    except Exception as e:
        st.error(f"❌ Error saving design state: {str(e)}")

def save_project_metadata(project_id):
    try:
        supabase.table('projects').update({
            'name': st.session_state.project_name,
            'client_name': st.session_state.client_name,
            'main_contractor': st.session_state.main_contractor,
            'contact_phone': st.session_state.contact_phone,
            'contact_email': st.session_state.contact_email,
            'project_date': str(st.session_state.project_date)
        }).eq('id', project_id).execute()
    except Exception as e:
        st.error(f"❌ Error saving project metadata: {str(e)}")

def unlock_project(project_id):
    try:
        supabase.table('projects').update({'design_state->>frozen': 'false'}).eq('id', project_id).execute()
        st.session_state.frozen = False
        st.success("✅ Project unlocked. You can now make changes.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error unlocking project: {str(e)}")

def delete_design_data(project_id):
    try:
        supabase.table('projects').update({'design_state': {}}).eq('id', project_id).execute()
        st.session_state.design_parameters = {}
        st.session_state.iteration_count = 0
        st.session_state.feedback_history = []
        st.session_state.frozen = False
        st.session_state.uploaded_images = []
        st.session_state.round = 0
        st.session_state.interpretation = None
        st.success("✅ All design data deleted. Project metadata preserved.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error deleting design data: {str(e)}")

def export_project_json(project_id, project_name):
    try:
        project = supabase.table('projects').select('*').eq('id', project_id).execute()
        if not project.data:
            return None, "Project not found"
        iterations = supabase.table('design_iterations').select('*').eq('project_id', project_id).execute()
        images = []
        for iter_data in iterations.data:
            img = supabase.table('images').select('*').eq('iteration_id', iter_data['id']).execute()
            images.extend(img.data)
        comments = []
        for iter_data in iterations.data:
            cmt = supabase.table('comments').select('*').eq('iteration_id', iter_data['id']).execute()
            comments.extend(cmt.data)
        export_data = {
            'project': project.data[0],
            'iterations': iterations.data,
            'images': images,
            'comments': comments,
            'exported_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        json_str = json.dumps(export_data, indent=2, default=str)
        return json_str, None
    except Exception as e:
        return None, str(e)

def export_images_zip(project_id):
    try:
        iterations = supabase.table('design_iterations').select('id').eq('project_id', project_id).execute()
        iteration_ids = [i['id'] for i in iterations.data]
        if not iteration_ids:
            return None, "No images found"
        images = supabase.table('images').select('*').in_('iteration_id', iteration_ids).execute()
        if not images.data:
            return None, "No images found"
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for img in images.data:
                try:
                    file_data = supabase.storage.from_('design-uploads').download(img['storage_path'])
                    filename = img.get('filename', f"image_{img['id']}.jpg")
                    zip_file.writestr(filename, file_data)
                except:
                    pass
        zip_buffer.seek(0)
        return zip_buffer, None
    except Exception as e:
        return None, str(e)

# ============================================================================
# Design Interpreter
# ============================================================================

def call_deepseek_api(prompt, api_key):
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a structural engineering design interpreter. Extract parameters: structure_type (Saddle Span, Single Pole, Canopy, Sail Structure), span (m), rise (m), laa (m), height (m), radius (m), supports (number), beams (number). Return ONLY JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return content, None
        else:
            return None, f"API Error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Request Error: {str(e)}"

def interpret_description(description):
    params = {
        'structure_type': 'Saddle Span',
        'span': 0.0,
        'rise': 0.0,
        'laa': 0.0,
        'height': 0,
        'radius': 0,
        'supports': 2,
        'beams': 2
    }
    
    text = description.lower()
    
    if 'saddle' in text or 'two curved' in text:
        params['structure_type'] = 'Saddle Span'
    elif 'single pole' in text or 'central pole' in text:
        params['structure_type'] = 'Single Pole'
    elif 'canopy' in text or 'four columns' in text:
        params['structure_type'] = 'Canopy'
    elif 'sail' in text or 'anchors' in text:
        params['structure_type'] = 'Sail Structure'
    
    import re
    span_matches = re.findall(r'(\d+\.?\d*)\s*(?:m|meter|meters)\s*(?:span|long|length)', text)
    if span_matches:
        params['span'] = float(span_matches[0])
    
    rise_matches = re.findall(r'(\d+\.?\d*)\s*(?:m|meter|meters)\s*(?:rise|height|tall|high)', text)
    if rise_matches:
        params['rise'] = float(rise_matches[0])
    
    width_matches = re.findall(r'(\d+\.?\d*)\s*(?:m|meter|meters)\s*(?:wide|width|apart|separation)', text)
    if width_matches:
        params['laa'] = float(width_matches[0])
    
    return params

def parse_ai_interpretation(response_text):
    try:
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            return data, None
        else:
            return None, "No JSON found."
    except json.JSONDecodeError as e:
        return None, f"JSON parsing error: {str(e)}"

# ============================================================================
# Geometry Engine – CORRECTED SADDLE SPAN (Defaults = 0)
# ============================================================================

def generate_geometry(structure_type, params):
    if structure_type == "Saddle Span":
        return generate_saddle_span(params)
    elif structure_type == "Single Pole":
        return generate_single_pole(params)
    elif structure_type == "Canopy":
        return generate_canopy(params)
    elif structure_type == "Sail Structure":
        return generate_sail(params)
    else:
        return generate_saddle_span(params)

def generate_saddle_span(params):
    span = params.get('span', 0.0)
    rise = params.get('rise', 0.0)
    laa = params.get('laa', 0.0)
    num_points = 30

    # Validate all parameters are positive
    if span <= 0 or rise <= 0 or laa <= 0:
        st.error("❌ Invalid parameters. Span, Rise, and LAA must be greater than 0.")
        st.info("Please go back and confirm your design interpretation with valid values.")
        return None

    # --- Beams ---
    x = np.linspace(-span/2, span/2, num_points)
    z = rise * (1 - (2 * x / span)**2)
    
    # Beam 1 (left side)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    # Beam 2 (right side)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    # --- Membrane Surface (SADDLE between beams) ---
    u = np.linspace(0, 1, num_points)  # along the span
    v = np.linspace(0, 1, num_points)  # between beams

    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, u_val in enumerate(u):
        for j, v_val in enumerate(v):
            # X position along span
            x_pos = -span/2 + u_val * span
            
            # Y position: interpolate between beam y1 and y2 at this x
            y_pos = y1[i] * (1 - v_val) + y2[i] * v_val
            
            # Z position: beam height at this x, then saddle effect
            z_beam = rise * (1 - (2 * x_pos / span)**2) if abs(x_pos) <= span/2 else 0
            # Saddle: lower in the middle between beams
            z_pos = z_beam * (1 - 0.3 * (2 * v_val - 1)**2)
            
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    # --- Apexes ---
    apex1 = (0, -laa/2, rise)
    apex2 = (0, laa/2, rise)

    # --- Supports ---
    supports = [(-span/2, 0, 0), (span/2, 0, 0)]

    return {
        'type': 'Saddle Span',
        'beams': [
            {'x': x.tolist(), 'y': y1.tolist(), 'z': z.tolist(), 'color': '#FF6B6B'},
            {'x': x.tolist(), 'y': y2.tolist(), 'z': z.tolist(), 'color': '#FF6B6B'}
        ],
        'apexes': [apex1, apex2],
        'supports': supports,
        'surface': (X_surf.tolist(), Y_surf.tolist(), Z_surf.tolist()),
        'dimensions': {'span': span, 'rise': rise, 'laa': laa}
    }

def generate_single_pole(params):
    height = params.get('height', 0.0)
    radius = params.get('radius', 0.0)
    num_points = 20
    
    if height <= 0 or radius <= 0:
        st.error("❌ Invalid parameters. Height and Radius must be greater than 0.")
        return None
    
    x = np.zeros(num_points * 2)
    y = np.zeros(num_points * 2)
    z = np.zeros(num_points * 2)
    
    x[:num_points] = 0
    y[:num_points] = 0
    z[:num_points] = np.linspace(0, height, num_points)
    
    theta = np.linspace(0, 2*np.pi, num_points)
    x[num_points:] = radius * np.cos(theta)
    y[num_points:] = radius * np.sin(theta)
    z[num_points:] = height * 0.95
    
    supports = [(0, 0, 0)]
    apexes = [(0, 0, height)]
    
    return {
        'type': 'Single Pole',
        'beams': [{'x': x.tolist(), 'y': y.tolist(), 'z': z.tolist(), 'color': '#8B8B8B'}],
        'apexes': apexes,
        'supports': supports,
        'surface': None,
        'dimensions': {'height': height, 'radius': radius}
    }

def generate_canopy(params):
    length = params.get('length', 0.0)
    width = params.get('width', 0.0)
    height = params.get('height', 0.0)
    
    if length <= 0 or width <= 0 or height <= 0:
        st.error("❌ Invalid parameters. Length, Width, and Height must be greater than 0.")
        return None
    
    corners = [
        (-length/2, -width/2, 0),
        (-length/2, width/2, 0),
        (length/2, -width/2, 0),
        (length/2, width/2, 0)
    ]
    
    supports = corners
    
    x = [-length/2, length/2, length/2, -length/2, -length/2]
    y = [-width/2, -width/2, width/2, width/2, -width/2]
    z = [height, height, height, height, height]
    
    return {
        'type': 'Canopy',
        'beams': [{'x': x, 'y': y, 'z': z, 'color': '#F5F5F5'}],
        'apexes': [],
        'supports': supports,
        'surface': None,
        'dimensions': {'length': length, 'width': width, 'height': height}
    }

def generate_sail(params):
    span = params.get('span', 0.0)
    n_anchors = params.get('n_anchors', 4)
    height = params.get('height', 0.0)
    
    if span <= 0 or n_anchors <= 0 or height <= 0:
        st.error("❌ Invalid parameters. Span, Anchors, and Height must be greater than 0.")
        return None
    
    anchors = []
    for i in range(n_anchors):
        angle = 2 * np.pi * i / n_anchors
        r = span / 2
        anchors.append((r * np.cos(angle), r * np.sin(angle), 0))
    
    apex = (0, 0, height)
    
    return {
        'type': 'Sail Structure',
        'beams': [],
        'apexes': [apex],
        'supports': anchors,
        'surface': None,
        'dimensions': {'span': span, 'n_anchors': n_anchors, 'height': height}
    }

def plot_flexible_geometry(geometry, view_mode='3D'):
    if geometry is None:
        return go.Figure()
    
    fig = go.Figure()
    
    for beam in geometry.get('beams', []):
        x = beam['x']
        y = beam['y']
        z = beam['z']
        color = beam.get('color', '#FF6B6B')
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            line=dict(color=color, width=6),
            name='Beam'
        ))
    
    for i, apex in enumerate(geometry.get('apexes', [])):
        fig.add_trace(go.Scatter3d(
            x=[apex[0]], y=[apex[1]], z=[apex[2]],
            mode='markers',
            marker=dict(color='#FFD93D', size=12, symbol='diamond'),
            name=f'Apex {i+1}'
        ))
    
    for i, supp in enumerate(geometry.get('supports', [])):
        fig.add_trace(go.Scatter3d(
            x=[supp[0]], y=[supp[1]], z=[supp[2]],
            mode='markers',
            marker=dict(color='#4ECDC4', size=12, symbol='circle'),
            name=f'Support {i+1}'
        ))
    
    if geometry.get('surface'):
        X_surf, Y_surf, Z_surf = geometry['surface']
        fig.add_trace(go.Surface(
            x=X_surf, y=Y_surf, z=Z_surf,
            colorscale=[[0, '#E8E8E8'], [1, '#F5F5F5']],
            opacity=0.7,
            name='Membrane',
            showscale=False,
            lighting=dict(ambient=0.6, diffuse=0.8, specular=0.3)
        ))
    
    scene_config = dict(
        bgcolor='#1E1E1E',
        xaxis=dict(title='Length (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        yaxis=dict(title='Width (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        zaxis=dict(title='Height (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        aspectmode='manual',
        aspectratio=dict(x=2.0, y=1.2, z=1.0)
    )
    
    camera_dict = dict(eye=dict(x=2.0, y=2.0, z=1.5))
    if view_mode == 'Plan (Top)':
        camera_dict = dict(eye=dict(x=0, y=0, z=3))
    elif view_mode == 'Front Elevation':
        camera_dict = dict(eye=dict(x=0, y=3, z=0))
    elif view_mode == 'Side Elevation':
        camera_dict = dict(eye=dict(x=3, y=0, z=0))
    
    fig.update_layout(
        scene=scene_config,
        scene_camera=camera_dict,
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#1E1E1E',
        margin=dict(l=0, r=0, t=0, b=0),
        height=550,
        showlegend=True,
        legend=dict(bgcolor='#2A2A2A', font=dict(color='#FFFFFF')),
        font=dict(color='#B0B0B0')
    )
    
    return fig

# ============================================================================
# App Layout – Title + Fullscreen Toggle
# ============================================================================

col_title, col_fs = st.columns([4, 1])
with col_title:
    st.title("🏗️ SDS Design Portal")
    st.caption("Structural Design | Describe, Interpret, Visualize, Refine")
with col_fs:
    if st.button("⛶ Full Screen" if not st.session_state.fullscreen else "⛶ Normal", key="fullscreen_toggle"):
        st.session_state.fullscreen = not st.session_state.fullscreen
        st.rerun()

if st.session_state.fullscreen:
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none !important; }
        .main > div { max-width: 100% !important; padding: 0 !important; }
        .block-container { max-width: 100% !important; padding: 0.5rem !important; margin: 0 !important; }
        .stApp { margin-left: 0 !important; }
        .element-container { width: 100% !important; }
        .st-emotion-cache-1v0mbdj { padding-top: 0.5rem !important; }
        .row-widget { width: 100% !important; }
        .plotly-graph-div { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: block !important; }
        .block-container { max-width: 1200px !important; padding-top: 2rem !important; }
        .main > div { max-width: 1200px !important; margin: 0 auto !important; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# STAGE 0: PROJECT DASHBOARD
# ============================================================================

if st.session_state.stage == 0:
    st.subheader("📋 Project Dashboard")
    try:
        projects = supabase.table('projects').select('id, name, client_name, project_date, created_by, design_state').order('created_at', desc=True).execute()
        projects_data = projects.data
        if projects_data:
            st.caption(f"Showing {len(projects_data)} project(s)")
            for proj in projects_data:
                state = proj.get('design_state', {})
                status = "🔓 Draft"
                if state.get('frozen', False):
                    status = "🔒 Frozen"
                elif state.get('confirmed', False):
                    status = "📋 Understanding Locked"
                st.markdown(f"""
                <div class="project-card">
                    <strong>{proj['name']}</strong><br>
                    <span>Client: {proj.get('client_name', 'N/A')} | Date: {proj.get('project_date', 'N/A')}</span><br>
                    <span>Status: {status} | Iterations: {state.get('iteration_count', 0)} | Rounds: {state.get('round', 0)}</span>
                </div>
                """, unsafe_allow_html=True)
                cols = st.columns([1, 1, 1, 1, 1])
                with cols[0]:
                    if st.button("📂 Load", key=f"load_{proj['id']}"):
                        st.session_state.load_project_id = proj['id']
                        st.session_state.load_project_name = proj['name']
                        st.session_state.stage = 0.5
                        st.rerun()
                with cols[1]:
                    if st.button("🔓 Unlock", key=f"unlock_{proj['id']}"):
                        unlock_project(proj['id'])
                with cols[2]:
                    if st.button("📥 Export JSON", key=f"export_{proj['id']}"):
                        json_data, error = export_project_json(proj['id'], proj['name'])
                        if json_data:
                            st.download_button(
                                label="⬇️ Download JSON",
                                data=json_data,
                                file_name=f"{proj['name']}_{proj['id'][:8]}.json",
                                mime="application/json",
                                key=f"download_{proj['id']}"
                            )
                with cols[3]:
                    if st.button("🗑️", key=f"delete_{proj['id']}"):
                        delete_project(proj['id'])
                with cols[4]:
                    if st.button("🖼️ Export Images", key=f"export_images_{proj['id']}"):
                        zip_data, error = export_images_zip(proj['id'])
                        if zip_data:
                            st.download_button(
                                label="⬇️ Download Images ZIP",
                                data=zip_data,
                                file_name=f"{proj['name']}_images.zip",
                                mime="application/zip",
                                key=f"download_zip_{proj['id']}"
                            )
                st.divider()
        else:
            st.info("No projects found. Create your first project below.")
    except Exception as e:
        st.error(f"❌ Error loading projects: {str(e)}")
    
    st.subheader("➕ Create New Project")
    if st.button("📤 New Project", type="primary"):
        st.session_state.stage = 1
        st.rerun()

# ============================================================================
# STAGE 0.5: LOAD OPTIONS
# ============================================================================

elif st.session_state.stage == 0.5:
    st.subheader("📂 Load Project Options")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    project_id = st.session_state.get('load_project_id', None)
    project_name = st.session_state.get('load_project_name', 'Unknown Project')
    if not project_id:
        st.error("Project ID not found.")
        st.session_state.stage = 0
        st.rerun()
    st.markdown(f"""
    <div class="load-options-card">
        <strong style="color: #FFFFFF;">📂 Project: {project_name}</strong><br>
        <span style="color: #D0D0D0;">Choose how you want to load this project.</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 🔄 What would you like to do?")
    if st.button("✅ Continue", key="load_continue"):
        try:
            result = supabase.table('projects').select('*').eq('id', project_id).execute()
            if result.data:
                data = result.data[0]
                state = data.get('design_state', {})
                st.session_state.project_id = project_id
                st.session_state.project_name = data.get('name', '')
                st.session_state.client_name = data.get('client_name', '')
                st.session_state.main_contractor = data.get('main_contractor', '')
                st.session_state.contact_phone = data.get('contact_phone', '')
                st.session_state.contact_email = data.get('contact_email', '')
                st.session_state.project_date = data.get('project_date', datetime.now().date())
                if isinstance(state, dict):
                    st.session_state.design_parameters = state.get('parameters', {})
                    st.session_state.iteration_count = state.get('iteration_count', 0)
                    st.session_state.feedback_history = state.get('feedback_history', [])
                    st.session_state.frozen = state.get('frozen', False)
                    st.session_state.uploaded_images = state.get('uploaded_images', [])
                    st.session_state.round = state.get('round', 0)
                    st.session_state.interpretation = state.get('interpretation', None)
                if state.get('frozen', False):
                    stage = 5
                elif state.get('confirmed', False):
                    stage = 3.0
                elif state.get('iteration_count', 0) > 0:
                    stage = 2.5
                else:
                    stage = 2
                st.session_state.stage = stage
                st.success("✅ Project loaded successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error loading project: {str(e)}")
    st.markdown("---")
    if st.button("🔄 Start Fresh", key="load_fresh"):
        try:
            supabase.table('projects').update({'design_state': {}}).eq('id', project_id).execute()
            st.session_state.project_id = project_id
            st.session_state.design_parameters = {}
            st.session_state.iteration_count = 0
            st.session_state.feedback_history = []
            st.session_state.frozen = False
            st.session_state.uploaded_images = []
            st.session_state.round = 0
            st.session_state.interpretation = None
            st.session_state.stage = 2
            st.success("✅ Design data deleted. Starting fresh.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    st.markdown("---")
    st.markdown("**3. Choose what to keep**")
    st.caption("Select which design data to restore.")
    try:
        result = supabase.table('projects').select('design_state').eq('id', project_id).execute()
        current_state = result.data[0].get('design_state', {}) if result.data else {}
    except:
        current_state = {}
    has_data = any([
        current_state.get('parameters', {}),
        current_state.get('feedback_history', []),
        current_state.get('iteration_count', 0) > 0
    ])
    if has_data:
        with st.form("load_selective"):
            keep_description = st.checkbox("📝 Description", value=True, key="keep_description")
            keep_parameters = st.checkbox("📐 Parameters", value=True, key="keep_parameters")
            keep_feedback = st.checkbox("📝 Feedback History", value=True, key="keep_feedback")
            keep_images = st.checkbox("🖼️ Uploaded Images", value=True, key="keep_images")
            keep_interpretation = st.checkbox("🧠 Interpretation", value=True, key="keep_interpretation")
            if st.form_submit_button("✅ Load Selected", type="primary"):
                new_state = {}
                if keep_description:
                    new_state['parameters'] = current_state.get('parameters', {})
                if keep_parameters:
                    for key in ['span', 'rise', 'laa', 'width', 'height', 'radius', 'length']:
                        if key in current_state.get('parameters', {}):
                            new_state['parameters'][key] = current_state['parameters'][key]
                if keep_feedback and current_state.get('feedback_history'):
                    new_state['feedback_history'] = current_state['feedback_history']
                if keep_images and current_state.get('uploaded_images'):
                    new_state['uploaded_images'] = current_state['uploaded_images']
                if keep_interpretation and current_state.get('interpretation'):
                    new_state['interpretation'] = current_state['interpretation']
                new_state['iteration_count'] = current_state.get('iteration_count', 0)
                new_state['frozen'] = current_state.get('frozen', False)
                new_state['round'] = current_state.get('round', 0)
                supabase.table('projects').update({'design_state': new_state}).eq('id', project_id).execute()
                st.session_state.project_id = project_id
                st.session_state.design_parameters = new_state.get('parameters', {})
                st.session_state.iteration_count = new_state.get('iteration_count', 0)
                st.session_state.feedback_history = new_state.get('feedback_history', [])
                st.session_state.frozen = new_state.get('frozen', False)
                st.session_state.uploaded_images = new_state.get('uploaded_images', [])
                st.session_state.round = new_state.get('round', 0)
                st.session_state.interpretation = new_state.get('interpretation', None)
                if new_state.get('frozen', False):
                    stage = 5
                elif new_state.get('confirmed', False):
                    stage = 3.0
                elif new_state.get('iteration_count', 0) > 0:
                    stage = 2.5
                else:
                    stage = 2
                st.session_state.stage = stage
                st.success("✅ Selected data restored successfully!")
                st.rerun()
    else:
        st.info("📭 No design data found.")

# ============================================================================
# STAGE 1: PROJECT REGISTRATION
# ============================================================================

elif st.session_state.stage == 1:
    st.subheader("📋 Project Registration")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    if st.button("🗑️ Clear All Fields", key="clear_stage1"):
        clear_stage_fields(1)
    with st.form("project_registration"):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name *", placeholder="e.g., Taman Megah Canopy", key="proj_name", value=st.session_state.get('project_name', ''))
            client_name = st.text_input("Client Name", placeholder="e.g., Tuan Haji Ahmad", key="client_name", value=st.session_state.get('client_name', ''))
            main_contractor = st.text_input("Main Contractor", placeholder="e.g., Bina Sdn Bhd", key="main_contractor", value=st.session_state.get('main_contractor', ''))
        with col2:
            contact_phone = st.text_input("Contact Phone", placeholder="e.g., 012-3456789", key="contact_phone", value=st.session_state.get('contact_phone', ''))
            contact_email = st.text_input("Contact Email", placeholder="e.g., client@email.com", key="contact_email", value=st.session_state.get('contact_email', ''))
            project_date = st.date_input("Project Date", value=st.session_state.get('project_date', datetime.now().date()), key="project_date")
            st.caption("📅 Auto-set to today")
        submitted = st.form_submit_button("📤 Register Project", type="primary")
        if submitted:
            if not project_name:
                st.error("❌ Project Name is required.")
            else:
                with st.spinner("Registering project..."):
                    try:
                        project_data = {
                            'name': project_name,
                            'client_name': client_name if client_name else None,
                            'main_contractor': main_contractor if main_contractor else None,
                            'contact_phone': contact_phone if contact_phone else None,
                            'contact_email': contact_email if contact_email else None,
                            'project_date': str(project_date),
                            'created_by': str(uuid.uuid4()),
                            'design_state': {}
                        }
                        result = supabase.table('projects').insert(project_data).execute()
                        st.session_state.project_id = result.data[0]['id']
                        st.session_state.project_name = project_name
                        st.session_state.client_name = client_name
                        st.session_state.main_contractor = main_contractor
                        st.session_state.contact_phone = contact_phone
                        st.session_state.contact_email = contact_email
                        st.session_state.project_date = project_date
                        st.session_state.stage = 2
                        st.success(f"✅ Project '{project_name}' registered successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Registration error: {str(e)}")

# ============================================================================
# STAGE 2: DESIGN INPUT
# ============================================================================

elif st.session_state.stage == 2:
    st.subheader("📐 Design Input")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    if st.button("🗑️ Clear All Fields", key="clear_stage2"):
        clear_stage_fields(2)
    
    st.markdown("""
    <div style="background-color: #2A3A4A; padding: 16px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid #00B4D8;">
        <strong style="color: #FFFFFF;">📋 How It Works</strong><br>
        <span style="color: #D0D0D0;">1. Upload images → 2. Describe your design → 3. Interpret → 4. Confirm → 5. Generate 3D model</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("design_input"):
        st.subheader("🖼️ Upload Images (Optional)")
        uploaded_files = st.file_uploader(
            "Choose images (JPG/PNG, max 10MB each)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="design_images",
            help="Upload sketches, photos of existing structures, or site inspiration"
        )
        if uploaded_files:
            st.success(f"📸 {len(uploaded_files)} image(s) uploaded")
            st.session_state.uploaded_images = [f.name for f in uploaded_files]
        elif st.session_state.uploaded_images:
            st.info(f"📸 Previously uploaded: {len(st.session_state.uploaded_images)} image(s)")
        
        st.subheader("📝 Describe Your Design")
        description = st.text_area(
            "Describe your design concept in natural language",
            placeholder="e.g., A saddle span tensile membrane structure spanning 10 meters with a rise of 6.5 meters. Two curved beams with separate apexes, 15 meters apart. Two pinned supports at the base.",
            key="description",
            height=200,
            value=st.session_state.design_parameters.get('description', '')
        )
        st.caption("💡 Be as detailed as possible. Include dimensions, materials, and structural elements.")
        
        use_ai = st.checkbox("🧠 Use AI for interpretation (optional)", key="use_ai_interpretation")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("📤 Interpret Design", type="primary")
        with col2:
            if use_ai:
                st.caption("📡 AI will analyze your description for more accurate parameters.")
        
        if submitted:
            if not description:
                st.error("❌ Please describe your design.")
            else:
                params = interpret_description(description)
                
                if use_ai:
                    try:
                        api_key = st.secrets["DEEPSEEK_API_KEY"]
                        st.session_state.interpretation_source = 'AI'
                        with st.spinner("🧠 Consulting AI for interpretation..."):
                            ai_prompt = f"""Interpret this design description and extract parameters:
                            Description: {description}
                            Return ONLY JSON with: structure_type, span (m), rise (m), laa (m)."""
                            
                            result, error = call_deepseek_api(ai_prompt, api_key)
                            if result:
                                ai_data, parse_error = parse_ai_interpretation(result)
                                if ai_data:
                                    for key, value in ai_data.items():
                                        if value is not None:
                                            params[key] = value
                                    st.session_state.interpretation_source = 'AI'
                                else:
                                    st.warning(f"⚠️ AI parsing issue: {parse_error}. Using simple parser instead.")
                                    st.session_state.interpretation_source = 'Parser'
                            else:
                                st.warning(f"⚠️ AI not available: {error}. Using simple parser.")
                                st.session_state.interpretation_source = 'Parser'
                    except:
                        st.session_state.interpretation_source = 'Parser'
                        st.info("💡 AI not configured. Using simple parser.")
                else:
                    st.session_state.interpretation_source = 'Parser'
                
                st.session_state.interpretation = params
                st.session_state.design_parameters = {
                    'description': description,
                    'interpretation': params,
                    'structure_type': params.get('structure_type', 'Saddle Span'),
                    'span': params.get('span', 0.0),
                    'rise': params.get('rise', 0.0),
                    'laa': params.get('laa', 0.0),
                    'height': 0,
                    'radius': 0,
                    'supports': params.get('supports', 2),
                    'beams': params.get('beams', 2)
                }
                st.session_state.iteration_count = 0
                st.session_state.feedback_history = []
                st.session_state.understanding_locked = False
                st.session_state.round = 0
                st.session_state.stage = 2.5
                save_design_state(st.session_state.project_id)
                save_project_metadata(st.session_state.project_id)
                st.rerun()

# ============================================================================
# STAGE 2.5: INTERPRETATION REVIEW
# ============================================================================

elif st.session_state.stage == 2.5:
    st.subheader("🧠 Design Interpretation")
    if st.button("⬅️ Back to Design Input"):
        st.session_state.stage = 2
        st.rerun()
    
    params = st.session_state.interpretation
    source = st.session_state.interpretation_source
    
    st.markdown(f"""
    <div class="interpretation-card">
        <strong style="color: #FFFFFF;">📋 Interpretation Summary</strong><br>
        <span style="color: #D0D0D0;">Source: {source}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background-color: #2A2A2A; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
        <strong style="color: #FFFFFF;">📐 Extracted Parameters:</strong><br>
        <span style="color: #D0D0D0;">Structure Type: {params.get('structure_type', 'N/A')}</span><br>
        <span style="color: #D0D0D0;">Span: {params.get('span', 0.0):.1f} m</span><br>
        <span style="color: #D0D0D0;">Rise: {params.get('rise', 0.0):.1f} m</span><br>
        <span style="color: #D0D0D0;">LAA: {params.get('laa', 0.0):.1f} m</span><br>
        <span style="color: #D0D0D0;">Supports: {params.get('supports', 2)}</span><br>
        <span style="color: #D0D0D0;">Beams: {params.get('beams', 2)}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ✏️ Confirm or Modify")
    st.caption("Adjust any parameter if the interpretation is not correct.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        structure_type = st.selectbox(
            "Structure Type",
            ["Saddle Span", "Single Pole", "Canopy", "Sail Structure"],
            index=["Saddle Span", "Single Pole", "Canopy", "Sail Structure"].index(params.get('structure_type', 'Saddle Span'))
        )
    with col2:
        span = st.number_input("Span (m)", value=params.get('span', 0.0), step=0.5)
    with col3:
        rise = st.number_input("Rise (m)", value=params.get('rise', 0.0), step=0.5)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        laa = st.number_input("LAA (m)", value=params.get('laa', 0.0), step=0.5)
    with col2:
        supports = st.number_input("Supports", value=params.get('supports', 2), step=1, min_value=1, max_value=20)
    with col3:
        beams = st.number_input("Beams", value=params.get('beams', 2), step=1, min_value=0, max_value=10)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Interpretation", type="primary"):
            st.session_state.design_parameters = {
                'description': st.session_state.design_parameters.get('description', ''),
                'structure_type': structure_type,
                'span': span,
                'rise': rise,
                'laa': laa,
                'height': 0,
                'radius': 0,
                'supports': supports,
                'beams': beams
            }
            st.session_state.interpretation = {
                'structure_type': structure_type,
                'span': span,
                'rise': rise,
                'laa': laa,
                'height': 0,
                'radius': 0,
                'supports': supports,
                'beams': beams
            }
            save_design_state(st.session_state.project_id)
            st.success("✅ Interpretation confirmed! Generating 3D model...")
            st.session_state.stage = 3.0
            st.rerun()
    
    with col2:
        if st.button("🔁 Go Back to Modify", type="secondary"):
            st.session_state.stage = 2
            st.rerun()

# ============================================================================
# STAGE 3.0: 3D MODEL VIEW
# ============================================================================

elif st.session_state.stage == 3.0:
    st.subheader("🏗️ 3D Design Model")
    if st.button("⬅️ Back to Interpretation"):
        st.session_state.stage = 2.5
        st.rerun()
    if st.button("💾 Save Progress", key="save_progress_30"):
        save_design_state(st.session_state.project_id)
        st.success("✅ Progress saved!")
    
    params = st.session_state.design_parameters
    structure_type = params.get('structure_type', 'Saddle Span')
    
    # Safeguard: Ensure correct structure type
    valid_types = ["Saddle Span", "Single Pole", "Canopy", "Sail Structure"]
    if structure_type not in valid_types:
        structure_type = "Saddle Span"
        st.warning("⚠️ Structure type reset to Saddle Span.")
    
    # Check for valid parameters
    span = params.get('span', 0.0)
    rise = params.get('rise', 0.0)
    laa = params.get('laa', 0.0)
    
    if span <= 0 or rise <= 0 or laa <= 0:
        st.error("❌ Invalid parameters. Span, Rise, and LAA must be greater than 0.")
        st.info("Please go back to the Interpretation stage and confirm valid values.")
        if st.button("⬅️ Go Back to Interpretation"):
            st.session_state.stage = 2.5
            st.rerun()
        st.stop()
    
    st.markdown(f"""
    <div style="background-color: #2A2A2A; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
        <strong style="color: #FFFFFF;">📐 {structure_type}</strong><br>
        <span style="color: #D0D0D0;">Span = {span:.1f}m | Rise = {rise:.1f}m | LAA = {laa:.1f}m</span>
    </div>
    """, unsafe_allow_html=True)
    
    view_modes = ['3D Perspective', 'Plan (Top)', 'Front Elevation', 'Side Elevation']
    selected_view = st.radio("View Mode", view_modes, horizontal=True, key="view_mode_30")
    
    with st.spinner("Building 3D model..."):
        geometry = generate_geometry(structure_type, params)
        if geometry is None:
            st.stop()
        fig = plot_flexible_geometry(geometry, selected_view)
        st.plotly_chart(fig, use_container_width=True, key="design_3d")
    
    st.info("✅ 3D model generated. Use the controls above to change view.")
    
    st.markdown("---")
    st.subheader("🔄 Refine Design")
    st.caption("Make adjustments to the design parameters.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        new_span = st.number_input("Span (m)", value=span, step=0.5, key="ref_span")
    with col2:
        new_rise = st.number_input("Rise (m)", value=rise, step=0.5, key="ref_rise")
    with col3:
        new_laa = st.number_input("LAA (m)", value=laa, step=0.5, key="ref_laa")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Update Model", type="primary"):
            st.session_state.design_parameters['span'] = new_span
            st.session_state.design_parameters['rise'] = new_rise
            st.session_state.design_parameters['laa'] = new_laa
            st.session_state.round += 1
            save_design_state(st.session_state.project_id)
            st.success("✅ Parameters updated! Rebuilding model...")
            st.rerun()
    
    with col2:
        if st.button("✅ Accept Design", type="secondary"):
            st.session_state.understanding_locked = True
            save_design_state(st.session_state.project_id)
            st.success("✅ Design accepted! Proceeding to collaboration.")
            st.session_state.stage = 3
            st.rerun()

# ============================================================================
# STAGE 3: COLLABORATION
# ============================================================================

elif st.session_state.stage == 3:
    st.subheader("💬 Collaboration")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    if st.button("🔓 Unlock for Editing", key="unlock_collab"):
        unlock_project(st.session_state.project_id)
    with st.form("collaboration"):
        stakeholder = st.selectbox("Communicate with", ["Owner", "Architect", "Engineer", "Other"], key="stakeholder")
        message = st.text_area("Your Message", placeholder="Share feedback, questions, or design ideas...", key="message")
        submitted = st.form_submit_button("📤 Send Message", type="primary")
        if submitted:
            with st.spinner("Sending message..."):
                try:
                    comment_data = {
                        'iteration_id': st.session_state.iteration_id,
                        'user_id': str(uuid.uuid4()),
                        'content': message,
                        'stakeholder_type': stakeholder,
                        'is_read': False
                    }
                    supabase.table('comments').insert(comment_data).execute()
                    st.success("✅ Message sent successfully!")
                except Exception as e:
                    st.error(f"❌ Error sending message: {str(e)}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to 3D Model"):
            st.session_state.stage = 3.0
            st.rerun()
    with col2:
        if st.button("📌 Freeze Concept"):
            st.session_state.stage = 5
            st.rerun()

# ============================================================================
# STAGE 5: CONCEPT FREEZE
# ============================================================================

elif st.session_state.stage == 5:
    st.subheader("📌 Freeze Concept")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    if st.button("🔓 Unlock for Editing", key="unlock_freeze"):
        unlock_project(st.session_state.project_id)
    st.warning("⚠️ Freezing the concept will lock this design version. No further edits will be allowed.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel", type="secondary"):
            st.session_state.stage = 3
            st.rerun()
    with col2:
        if st.button("✅ Confirm Freeze", type="primary"):
            with st.spinner("Freezing concept..."):
                try:
                    supabase.table('projects').update({'design_state->>frozen': 'true'}).eq('id', st.session_state.project_id).execute()
                    st.session_state.frozen = True
                    save_design_state(st.session_state.project_id)
                    st.success("✅ Concept frozen successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error freezing concept: {str(e)}")
    if st.session_state.frozen:
        st.info("🎉 Your design is now frozen and ready for the next stage.")
        if st.button("🔄 Start New Project"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("🧬 Knowledge may evolve. 🌱 Identity shall remain.")
st.caption("SDS Chamber 002 – Design Portal")
