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
if 'typology' not in st.session_state:
    st.session_state.typology = 'Saddle Span'
if 'columns' not in st.session_state:
    st.session_state.columns = []
if 'iteration_count' not in st.session_state:
    st.session_state.iteration_count = 0
if 'feedback_history' not in st.session_state:
    st.session_state.feedback_history = []
if 'ai_bridge_response' not in st.session_state:
    st.session_state.ai_bridge_response = ''
if 'ai_bridge_prompt' not in st.session_state:
    st.session_state.ai_bridge_prompt = ''
if 'design_brief' not in st.session_state:
    st.session_state.design_brief = None
if 'design_brief_confirmed' not in st.session_state:
    st.session_state.design_brief_confirmed = False
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False
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

# ============================================================================
# Helper Functions
# ============================================================================

def clear_stage_fields(stage):
    keys_to_clear = []
    if stage == 1:
        keys_to_clear = ['proj_name', 'client_name', 'main_contractor', 'contact_phone', 'contact_email', 'project_date']
    elif stage == 2:
        keys_to_clear = ['description', 'typology']
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
                st.session_state.design_brief = state.get('design_brief', None)
                st.session_state.design_brief_confirmed = state.get('confirmed', False)
                st.session_state.frozen = state.get('frozen', False)
                st.session_state.ai_bridge_prompt = state.get('ai_prompt', '')
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
        'design_brief': st.session_state.design_brief,
        'confirmed': st.session_state.design_brief_confirmed,
        'frozen': st.session_state.frozen,
        'ai_prompt': st.session_state.ai_bridge_prompt,
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
    """Delete all design data from the project (keep metadata)."""
    try:
        # Reset design state
        supabase.table('projects').update({'design_state': {}}).eq('id', project_id).execute()
        # Reset session state
        st.session_state.design_parameters = {}
        st.session_state.iteration_count = 0
        st.session_state.feedback_history = []
        st.session_state.design_brief = None
        st.session_state.design_brief_confirmed = False
        st.session_state.frozen = False
        st.session_state.ai_bridge_prompt = ''
        st.session_state.ai_bridge_response = ''
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
# DeepSeek API Integration
# ============================================================================

def call_deepseek_api(prompt, api_key):
    """Call DeepSeek API with the given prompt."""
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a structural engineering design expert. You MUST output ONLY valid JSON. No explanations, no markdown, just pure JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2000
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

def generate_ai_consultant_prompt(description, parameters):
    typology = parameters.get('typology', 'Saddle Span')
    A = parameters.get('A', 10.0)
    B = parameters.get('B', 5.0)
    LAA = parameters.get('LAA', 10.0)
    
    prompt = f"""You are an expert structural engineering design consultant specializing in tensile membrane structures.

**Your Role:**
Understand the user's design and produce a complete Design Brief in JSON format.

**Design Context:**
- Typology: {typology}
- Rise/Height (A): {A:.1f} m
- Plan/Horizontal (B): {B:.1f} m
- Apex-to-Apex (LAA): {LAA:.1f} m

**User's Description:**
{description}

**Required JSON Structure (ONLY OUTPUT THIS EXACT FORMAT):**
{{
  "typology": "{typology}",
  "parameters": {{
    "A": {A:.1f},
    "B": {B:.1f},
    "LAA": {LAA:.1f}
  }},
  "beams": {{
    "orientation": "parallel",
    "section": "CHS 219 x 6.3",
    "material": "Steel"
  }},
  "membrane": {{
    "type": "PVC/PTFE",
    "prestress": "3.0 kN/m",
    "attachment": "continuous_slot"
  }},
  "supports": {{
    "type": "pinned",
    "base_plate": "steel"
  }},
  "columns": {{
    "count": 4,
    "heights": [3.0, 3.0, 3.0, 3.0]
  }},
  "refinements": {{
    "add_beams": false,
    "adjust_apex": false
  }}
}}

**OUTPUT ONLY THE JSON OBJECT. NO OTHER TEXT.**"""
    return prompt

def parse_design_brief(response_text):
    """Extract and parse JSON from AI response."""
    try:
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            return data, None
        else:
            return None, "No JSON found in response. Please ensure the AI outputs valid JSON."
    except json.JSONDecodeError as e:
        return None, f"JSON parsing error: {str(e)}. Please check the format."

# ============================================================================
# Parametric 3D Engine (Saddle Span)
# ============================================================================

def generate_saddle_span_geometry(A, B, LAA, num_points=30):
    x1 = np.linspace(-LAA/2, LAA/2, num_points)
    z1 = A * (1 - (2 * x1 / LAA)**2)
    y1 = np.zeros_like(x1)
    x2 = np.linspace(-LAA/2, LAA/2, num_points)
    z2 = A * (1 - (2 * x2 / LAA)**2)
    y2 = np.full_like(x2, B)
    apex1 = (0, 0, A)
    apex2 = (0, B, A)
    support1 = (-LAA/2, 0, 0)
    support2 = (LAA/2, 0, 0)
    support3 = (-LAA/2, B, 0)
    support4 = (LAA/2, B, 0)
    u = np.linspace(0, 1, num_points)
    v = np.linspace(0, 1, num_points)
    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))
    for i, u_val in enumerate(u):
        for j, v_val in enumerate(v):
            x_pos = -LAA/2 + u_val * LAA
            y_pos = v_val * B
            z_beam1 = A * (1 - (2 * x_pos / LAA)**2) if abs(x_pos) <= LAA/2 else 0
            z_beam2 = A * (1 - (2 * x_pos / LAA)**2) if abs(x_pos) <= LAA/2 else 0
            z_surface = z_beam1 * (1 - v_val) + z_beam2 * v_val
            z_saddle = z_surface + 0.1 * A * v_val * (1 - v_val) * (1 - (2 * u_val - 1)**2)
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_saddle
    return {
        'beam1': (x1, y1, z1),
        'beam2': (x2, y2, z2),
        'apex1': apex1,
        'apex2': apex2,
        'supports': [support1, support2, support3, support4],
        'surface': (X_surf, Y_surf, Z_surf)
    }

def plot_saddle_span_geometry(geometry, view_mode='3D'):
    x1, y1, z1 = geometry['beam1']
    x2, y2, z2 = geometry['beam2']
    apex1 = geometry['apex1']
    apex2 = geometry['apex2']
    supports = geometry['supports']
    X_surf, Y_surf, Z_surf = geometry['surface']
    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#E8E8E8'], [1, '#F5F5F5']],
        opacity=0.7, name='Membrane', showscale=False,
        lighting=dict(ambient=0.6, diffuse=0.8, specular=0.3)
    ))
    fig.add_trace(go.Scatter3d(x=x1, y=y1, z=z1, mode='lines', line=dict(color='#FF6B6B', width=8), name='Beam 1'))
    fig.add_trace(go.Scatter3d(x=x2, y=y2, z=z2, mode='lines', line=dict(color='#FF6B6B', width=8), name='Beam 2'))
    fig.add_trace(go.Scatter3d(x=[apex1[0]], y=[apex1[1]], z=[apex1[2]], mode='markers', marker=dict(color='#FFD93D', size=12, symbol='diamond'), name='Apex 1'))
    fig.add_trace(go.Scatter3d(x=[apex2[0]], y=[apex2[1]], z=[apex2[2]], mode='markers', marker=dict(color='#FFD93D', size=12, symbol='diamond'), name='Apex 2'))
    for i, supp in enumerate(supports):
        fig.add_trace(go.Scatter3d(x=[supp[0]], y=[supp[1]], z=[supp[2]], mode='markers', marker=dict(color='#4ECDC4', size=10), name=f'Support {i+1}'))
    # Dimension lines
    fig.add_trace(go.Scatter3d(x=[apex1[0], apex1[0]], y=[apex1[1], apex1[1]], z=[0, apex1[2]], mode='lines', line=dict(color='#FFD93D', width=2, dash='dash'), name='A (Rise)'))
    fig.add_trace(go.Scatter3d(x=[apex1[0]+0.5], y=[apex1[1]+0.5], z=[apex1[2]/2], mode='text', text=[f"A = {apex1[2]:.1f}m"], textfont=dict(color='#FFD93D', size=12), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[supports[0][0], supports[2][0]], y=[supports[0][1], supports[2][1]], z=[0, 0], mode='lines', line=dict(color='#4ECDC4', width=2, dash='dash'), name='B (Plan)'))
    fig.add_trace(go.Scatter3d(x=[supports[0][0]+0.5], y=[supports[0][1]+0.5], z=[0.5], mode='text', text=[f"B = {geometry['apex2'][1]:.1f}m"], textfont=dict(color='#4ECDC4', size=12), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[apex1[0], apex2[0]], y=[apex1[1], apex2[1]], z=[apex1[2], apex2[2]], mode='lines', line=dict(color='#FF6B6B', width=2, dash='dash'), name='LAA'))
    fig.add_trace(go.Scatter3d(x=[(apex1[0]+apex2[0])/2], y=[(apex1[1]+apex2[1])/2+0.5], z=[apex1[2]], mode='text', text=[f"LAA = {abs(apex1[0]-apex2[0]):.1f}m"], textfont=dict(color='#FF6B6B', size=12), showlegend=False))
    scene_config = dict(
        bgcolor='#1E1E1E',
        xaxis=dict(title='Length (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        yaxis=dict(title='Width (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        zaxis=dict(title='Height (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        aspectmode='manual', aspectratio=dict(x=1.5, y=0.8, z=1.0)
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
    st.caption("Tensile Membrane Structure Design | Multi-Stage Input Portal")
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
                    <span>Status: {status} | Iterations: {state.get('iteration_count', 0)}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Load Options – With User Control
                cols = st.columns([1, 1, 1, 1, 1])
                with cols[0]:
                    if st.button("📂 Load", key=f"load_{proj['id']}"):
                        st.session_state.load_project_id = proj['id']
                        st.session_state.load_project_name = proj['name']
                        st.session_state.stage = 0.5  # Load Options Stage
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
# STAGE 0.5: LOAD OPTIONS (User-Controlled Restoration)
# ============================================================================

elif st.session_state.stage == 0.5:
    st.subheader("📂 Load Project Options")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    
    project_id = st.session_state.get('load_project_id', None)
    project_name = st.session_state.get('load_project_name', 'Unknown Project')
    
    if not project_id:
        st.error("Project ID not found. Please go back and try again.")
        st.session_state.stage = 0
        st.rerun()
    
    st.markdown(f"""
    <div class="load-options-card">
        <strong style="color: #FFFFFF;">📂 Project: {project_name}</strong><br>
        <span style="color: #D0D0D0;">Choose how you want to load this project.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔄 What would you like to do?")
    
    # Option 1: Continue
    with st.container():
        st.markdown("**1. Continue from where you left off**")
        st.caption("Restore all data – description, parameters, AI prompts, Design Brief, 3D model, feedback history.")
        if st.button("✅ Continue", key="load_continue"):
            # Load all data
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
                        st.session_state.design_brief = state.get('design_brief', None)
                        st.session_state.design_brief_confirmed = state.get('confirmed', False)
                        st.session_state.frozen = state.get('frozen', False)
                        st.session_state.ai_bridge_prompt = state.get('ai_prompt', '')
                    
                    # Determine stage
                    if state.get('frozen', False):
                        stage = 5
                    elif state.get('confirmed', False):
                        stage = 2.9
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
    
    # Option 2: Start Fresh
    with st.container():
        st.markdown("**2. Start fresh (keep project name only)**")
        st.caption("Delete all design data (description, parameters, AI responses, Design Brief, 3D model). Only project metadata will remain.")
        st.warning("⚠️ This action cannot be undone.")
        if st.button("🔄 Start Fresh", key="load_fresh"):
            # Delete design data, keep metadata
            try:
                supabase.table('projects').update({'design_state': {}}).eq('id', project_id).execute()
                
                # Reset session state
                st.session_state.project_id = project_id
                st.session_state.design_parameters = {}
                st.session_state.iteration_count = 0
                st.session_state.feedback_history = []
                st.session_state.design_brief = None
                st.session_state.design_brief_confirmed = False
                st.session_state.frozen = False
                st.session_state.ai_bridge_prompt = ''
                st.session_state.ai_bridge_response = ''
                st.session_state.stage = 2
                st.success("✅ Design data deleted. Starting fresh.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting design data: {str(e)}")
    
    st.markdown("---")
    
    # Option 3: Choose What to Keep
    with st.container():
        st.markdown("**3. Choose what to keep**")
        st.caption("Select which design data to restore. Unchecked items will be deleted.")
        
        # Fetch current design state
        try:
            result = supabase.table('projects').select('design_state').eq('id', project_id).execute()
            current_state = result.data[0].get('design_state', {}) if result.data else {}
        except:
            current_state = {}
        
        # Check if there is any data
        has_data = any([
            current_state.get('parameters', {}),
            current_state.get('design_brief'),
            current_state.get('feedback_history', []),
            current_state.get('ai_prompt'),
            current_state.get('iteration_count', 0) > 0
        ])
        
        if has_data:
            with st.form("load_selective"):
                st.markdown("**Select what to restore:**")
                
                keep_description = st.checkbox("📝 Description", value=True, key="keep_description")
                keep_parameters = st.checkbox("📐 Parameters (A, B, LAA)", value=True, key="keep_parameters")
                keep_typology = st.checkbox("🏗️ Typology", value=True, key="keep_typology")
                keep_ai_prompt = st.checkbox("🤖 AI Prompt", value=True, key="keep_ai_prompt")
                keep_design_brief = st.checkbox("📋 Design Brief", value=True, key="keep_design_brief")
                keep_feedback = st.checkbox("📝 Feedback History", value=True, key="keep_feedback")
                
                st.caption("📌 Project metadata (name, client, contractor, contact info) will always be restored.")
                
                if st.form_submit_button("✅ Load Selected", type="primary"):
                    # Build new state from selected items
                    new_state = {}
                    
                    if keep_description and 'description' in current_state.get('parameters', {}):
                        new_state['parameters'] = new_state.get('parameters', {})
                        new_state['parameters']['description'] = current_state['parameters'].get('description')
                    if keep_parameters:
                        new_state['parameters'] = new_state.get('parameters', {})
                        for key in ['A', 'B', 'LAA']:
                            if key in current_state.get('parameters', {}):
                                new_state['parameters'][key] = current_state['parameters'][key]
                    if keep_typology and 'typology' in current_state.get('parameters', {}):
                        new_state['parameters'] = new_state.get('parameters', {})
                        new_state['parameters']['typology'] = current_state['parameters'].get('typology')
                    
                    if keep_ai_prompt and current_state.get('ai_prompt'):
                        new_state['ai_prompt'] = current_state['ai_prompt']
                    
                    if keep_design_brief and current_state.get('design_brief'):
                        new_state['design_brief'] = current_state['design_brief']
                        new_state['confirmed'] = True
                    
                    if keep_feedback and current_state.get('feedback_history'):
                        new_state['feedback_history'] = current_state['feedback_history']
                    
                    # Keep iteration count and frozen status
                    new_state['iteration_count'] = current_state.get('iteration_count', 0)
                    new_state['frozen'] = current_state.get('frozen', False)
                    new_state['last_modified'] = datetime.now().isoformat()
                    
                    # Update project
                    supabase.table('projects').update({'design_state': new_state}).eq('id', project_id).execute()
                    
                    # Update session state
                    st.session_state.project_id = project_id
                    st.session_state.design_parameters = new_state.get('parameters', {})
                    st.session_state.iteration_count = new_state.get('iteration_count', 0)
                    st.session_state.feedback_history = new_state.get('feedback_history', [])
                    st.session_state.design_brief = new_state.get('design_brief', None)
                    st.session_state.design_brief_confirmed = new_state.get('confirmed', False)
                    st.session_state.frozen = new_state.get('frozen', False)
                    st.session_state.ai_bridge_prompt = new_state.get('ai_prompt', '')
                    
                    # Determine stage
                    if new_state.get('frozen', False):
                        stage = 5
                    elif new_state.get('confirmed', False):
                        stage = 2.9
                    elif new_state.get('iteration_count', 0) > 0:
                        stage = 2.5
                    else:
                        stage = 2
                    
                    st.session_state.stage = stage
                    st.success("✅ Selected data restored successfully!")
                    st.rerun()
        else:
            st.info("📭 No design data found for this project. You can start fresh.")
            if st.button("📤 Start Fresh", key="load_fresh_empty"):
                try:
                    supabase.table('projects').update({'design_state': {}}).eq('id', project_id).execute()
                    st.session_state.project_id = project_id
                    st.session_state.design_parameters = {}
                    st.session_state.iteration_count = 0
                    st.session_state.feedback_history = []
                    st.session_state.design_brief = None
                    st.session_state.design_brief_confirmed = False
                    st.session_state.frozen = False
                    st.session_state.ai_bridge_prompt = ''
                    st.session_state.ai_bridge_response = ''
                    st.session_state.stage = 2
                    st.success("✅ Starting fresh.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

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
    
    # Pre-fill from session state if available
    params = st.session_state.design_parameters
    default_desc = params.get('description', '')
    default_typology = params.get('typology', 'Saddle Span')
    default_A = params.get('A', 10.0)
    default_B = params.get('B', 5.0)
    default_LAA = params.get('LAA', 10.0)
    
    with st.form("design_input"):
        st.subheader("📝 General Description")
        description = st.text_area(
            "Describe your design concept",
            placeholder="e.g., Two curved primary beams with a membrane roof...",
            key="description",
            height=150,
            value=default_desc
        )
        st.subheader("🏗️ Structural Typology")
        typology = st.selectbox(
            "Select Typology",
            ["Saddle Span", "Aluminium Free Span Tent", "Factory Warehouse", "Canopy (4 Columns)", "Sail Structure"],
            key="typology",
            index=["Saddle Span", "Aluminium Free Span Tent", "Factory Warehouse", "Canopy (4 Columns)", "Sail Structure"].index(default_typology) if default_typology in ["Saddle Span", "Aluminium Free Span Tent", "Factory Warehouse", "Canopy (4 Columns)", "Sail Structure"] else 0
        )
        st.subheader("📐 Parameters")
        col1, col2 = st.columns(2)
        with col1:
            A = st.number_input("Rise/Height (m)", value=default_A, step=0.5, key="A")
            B = st.number_input("Plan/Horizontal (m)", value=default_B, step=0.5, key="B")
        with col2:
            LAA = st.number_input("Apex-to-Apex (m)", value=default_LAA, step=0.5, key="LAA")
        
        st.caption("📐 These parameters define the primary geometry of the structure.")
        submitted = st.form_submit_button("📤 Proceed to AI Consultation", type="primary")
        if submitted:
            if not description:
                st.error("❌ Please enter a description.")
            else:
                st.session_state.design_parameters = {
                    'description': description,
                    'typology': typology,
                    'A': A, 'B': B, 'LAA': LAA
                }
                st.session_state.ai_bridge_prompt = generate_ai_consultant_prompt(description, st.session_state.design_parameters)
                st.session_state.iteration_count = 0
                st.session_state.feedback_history = []
                st.session_state.design_brief = None
                st.session_state.design_brief_confirmed = False
                save_design_state(st.session_state.project_id)
                save_project_metadata(st.session_state.project_id)
                st.session_state.stage = 2.5
                st.rerun()

# ============================================================================
# STAGE 2.5: AI CONSULTANT (AUTO-CALL + FALLBACK)
# ============================================================================

elif st.session_state.stage == 2.5:
    st.subheader("🧠 AI Consultant")
    if st.button("⬅️ Back to Design Input"):
        st.session_state.stage = 2
        st.rerun()
    
    st.markdown(f"""
    <div style="background-color: #2A2A2A; padding: 16px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid #00B4D8;">
        <strong style="color: #FFFFFF;">📝 Your Description:</strong><br>
        <span style="color: #D0D0D0;">{st.session_state.design_parameters.get('description', 'No description')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🤖 AI Consultant")
    st.caption("The app will automatically call DeepSeek to generate the Design Brief.")
    
    st.info(f"🔄 Iteration {st.session_state.iteration_count + 1}")
    
    if st.session_state.feedback_history:
        st.markdown("**📋 Feedback History:**")
        for i, fb in enumerate(st.session_state.feedback_history):
            st.caption(f"Iteration {i+1}: {fb[:100]}...")
    
    prompt = st.session_state.ai_bridge_prompt
    with st.expander("📋 View Prompt (Advanced)"):
        st.text_area("AI Consultant Prompt", prompt, height=200, key="ai_prompt_display")
    
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
        has_api_key = True
    except:
        has_api_key = False
        st.warning("⚠️ DeepSeek API key not found. Please add it to Streamlit Secrets.")
        st.info("💡 If you prefer, you can still use the manual copy-paste method below.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚀 Generate Design Brief", type="primary"):
            if has_api_key:
                with st.spinner("🤖 Calling DeepSeek API..."):
                    result, error = call_deepseek_api(prompt, api_key)
                    if result:
                        st.success("✅ DeepSeek response received!")
                        data, parse_error = parse_design_brief(result)
                        if data:
                            st.session_state.design_brief = data
                            st.session_state.design_brief_confirmed = False
                            st.session_state.iteration_count += 1
                            save_design_state(st.session_state.project_id)
                            st.success("✅ Design Brief extracted successfully!")
                            st.session_state.stage = 2.7
                            st.rerun()
                        else:
                            st.error(f"❌ Error parsing Design Brief: {parse_error}")
                            st.text_area("Raw Response (for debugging)", result, height=150)
                    else:
                        st.error(f"❌ API Error: {error}")
                        st.info("💡 You can use the manual fallback below.")
            else:
                st.error("❌ No API key found. Please add DEEPSEEK_API_KEY to Streamlit Secrets.")
    
    with col2:
        if st.button("📝 Manual Fallback", type="secondary"):
            st.session_state.stage = 2.6
            st.rerun()
    
    st.markdown("---")
    st.caption("📝 If you don't want to use AI, you can skip to manual design input.")
    if st.button("📝 Skip to Manual Design", key="skip_ai"):
        st.session_state.design_brief = {
            'typology': st.session_state.design_parameters.get('typology', 'Saddle Span'),
            'parameters': {
                'A': st.session_state.design_parameters.get('A', 10.0),
                'B': st.session_state.design_parameters.get('B', 5.0),
                'LAA': st.session_state.design_parameters.get('LAA', 10.0)
            },
            'beams': {'orientation': 'parallel', 'section': 'CHS 219 x 6.3', 'material': 'Steel'},
            'membrane': {'type': 'PVC/PTFE', 'prestress': '3.0 kN/m', 'attachment': 'continuous_slot'},
            'supports': {'type': 'pinned', 'base_plate': 'steel'},
            'columns': {'count': 4, 'heights': [3.0, 3.0, 3.0, 3.0]},
            'refinements': {'add_beams': False, 'adjust_apex': False}
        }
        st.session_state.design_brief_confirmed = True
        st.session_state.stage = 2.7
        st.rerun()

# ============================================================================
# STAGE 2.6: MANUAL FALLBACK
# ============================================================================

elif st.session_state.stage == 2.6:
    st.subheader("📝 Manual Fallback")
    if st.button("⬅️ Back to AI Consultant"):
        st.session_state.stage = 2.5
        st.rerun()
    
    st.caption("Copy the prompt below, paste it into your AI, and paste the response back.")
    
    prompt = st.session_state.ai_bridge_prompt
    st.text_area("AI Consultant Prompt", prompt, height=200, key="ai_prompt_fallback")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Copy Prompt", key="copy_prompt_fallback"):
            st.code(prompt, language="text")
            st.caption("✅ Prompt copied!")
    
    st.markdown("---")
    st.markdown("### 📥 Paste AI Response")
    ai_response = st.text_area("AI Response", placeholder="Paste the AI's response here...", height=150, key="ai_response_fallback")
    
    if st.button("🔄 Process Design Brief", type="primary"):
        if ai_response:
            data, error = parse_design_brief(ai_response)
            if data:
                st.session_state.design_brief = data
                st.session_state.design_brief_confirmed = False
                st.session_state.iteration_count += 1
                save_design_state(st.session_state.project_id)
                st.success("✅ Design Brief extracted successfully!")
                st.session_state.stage = 2.7
                st.rerun()
            else:
                st.error(f"❌ Error parsing Design Brief: {error}")
        else:
            st.error("❌ Please paste the AI response first.")

# ============================================================================
# STAGE 2.7: CONFIRM DESIGN BRIEF
# ============================================================================

elif st.session_state.stage == 2.7:
    st.subheader("📋 Review Design Brief")
    if st.button("⬅️ Back to AI Consultant"):
        st.session_state.stage = 2.5
        st.rerun()
    if st.button("💾 Save Progress", key="save_progress"):
        save_design_state(st.session_state.project_id)
        st.success("✅ Progress saved!")
    
    if st.session_state.design_brief:
        st.markdown("**Design Brief:**")
        st.json(st.session_state.design_brief)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁 Modify with Feedback", type="secondary"):
                st.session_state.stage = 2.8
                st.rerun()
        with col2:
            if st.button("✅ Confirm Design Brief", type="primary"):
                st.session_state.design_brief_confirmed = True
                save_design_state(st.session_state.project_id)
                st.success("✅ Design Brief confirmed!")
                st.session_state.stage = 2.9
                st.rerun()
    else:
        st.warning("No Design Brief found. Please go back to AI Consultant.")

# ============================================================================
# STAGE 2.8: PROVIDE FEEDBACK
# ============================================================================

elif st.session_state.stage == 2.8:
    st.subheader("📝 Provide Feedback")
    if st.button("⬅️ Back to Review"):
        st.session_state.stage = 2.7
        st.rerun()
    
    st.markdown("### 🔄 Feedback to AI Consultant")
    st.caption("Provide feedback on the Design Brief. The AI will refine it based on your feedback.")
    
    if st.session_state.design_brief:
        st.markdown("**Current Design Brief:**")
        st.json(st.session_state.design_brief)
    
    feedback = st.text_area("Your Feedback", placeholder="e.g., The beams should be diverging, not parallel. The rise should be 8m instead of 10m.", height=150, key="feedback_input")
    
    if st.button("🔄 Submit Feedback & Regenerate", type="primary"):
        if feedback:
            st.session_state.feedback_history.append(feedback)
            current_prompt = st.session_state.ai_bridge_prompt
            updated_prompt = current_prompt + f"\n\n**User Feedback:**\n{feedback}\n\nPlease update the Design Brief based on this feedback."
            st.session_state.ai_bridge_prompt = updated_prompt
            st.session_state.iteration_count += 1
            save_design_state(st.session_state.project_id)
            st.success("✅ Feedback submitted! Return to AI Consultant to regenerate.")
            st.session_state.stage = 2.5
            st.rerun()
        else:
            st.error("❌ Please enter feedback.")

# ============================================================================
# STAGE 2.9: PARAMETRIC 3D MODEL
# ============================================================================

elif st.session_state.stage == 2.9:
    st.subheader("🏗️ Parametric 3D Model")
    if st.button("⬅️ Back to Design Brief"):
        st.session_state.stage = 2.7
        st.rerun()
    if st.button("📐 Redesign & Refine"):
        st.session_state.stage = 3.0
        st.rerun()
    if st.button("💾 Save Progress", key="save_progress_2"):
        save_design_state(st.session_state.project_id)
        st.success("✅ Progress saved!")
    
    if st.session_state.design_brief:
        params = st.session_state.design_brief.get('parameters', {})
        A = params.get('A', 10.0)
        B = params.get('B', 5.0)
        LAA = params.get('LAA', 10.0)
        typology = st.session_state.design_brief.get('typology', 'Saddle Span')
    else:
        params = st.session_state.design_parameters
        A = params.get('A', 10.0)
        B = params.get('B', 5.0)
        LAA = params.get('LAA', 10.0)
        typology = params.get('typology', 'Saddle Span')
    
    st.markdown(f"""
    <div style="background-color: #2A2A2A; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
        <strong style="color: #FFFFFF;">📐 Confirmed Parameters:</strong><br>
        <span style="color: #D0D0D0;">Rise (A) = {A:.1f}m | Plan (B) = {B:.1f}m | LAA = {LAA:.1f}m</span><br>
        <span style="color: #D0D0D0;">Typology: {typology}</span>
    </div>
    """, unsafe_allow_html=True)
    
    view_modes = ['3D Perspective', 'Plan (Top)', 'Front Elevation', 'Side Elevation']
    selected_view = st.radio("View Mode", view_modes, horizontal=True, key="view_mode_29")
    
    with st.spinner("Generating 3D model..."):
        geometry = generate_saddle_span_geometry(A, B, LAA)
        fig = plot_saddle_span_geometry(geometry, selected_view)
        st.plotly_chart(fig, use_container_width=True, key="parametric_3d")
    
    st.info("✅ 3D model generated. Use the controls above to change view.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Design Brief", type="secondary"):
            st.session_state.stage = 2.7
            st.rerun()
    with col2:
        if st.button("📐 Redesign & Refine", type="primary"):
            st.session_state.stage = 3.0
            st.rerun()
    
    if st.button("📌 Proceed to Collaboration"):
        st.session_state.stage = 3
        st.rerun()

# ============================================================================
# STAGE 3.0: REDESIGN & REFINEMENT
# ============================================================================

elif st.session_state.stage == 3.0:
    st.subheader("📐 Redesign & Refinement")
    if st.button("⬅️ Back to 3D Model"):
        st.session_state.stage = 2.9
        st.rerun()
    
    params = st.session_state.design_brief.get('parameters', {}) if st.session_state.design_brief else st.session_state.design_parameters
    st.subheader("⚙️ Edit Geometry")
    with st.form("refinement_form"):
        col1, col2 = st.columns(2)
        with col1:
            A_new = st.number_input("Rise/Height (m)", value=params.get('A', 10.0), step=0.5, key="A_edit")
            B_new = st.number_input("Plan/Horizontal (m)", value=params.get('B', 5.0), step=0.5, key="B_edit")
        with col2:
            LAA_new = st.number_input("Apex-to-Apex (m)", value=params.get('LAA', 10.0), step=0.5, key="LAA_edit")
        st.subheader("🏗️ Columns")
        col_count = st.number_input("Number of Columns", min_value=0, max_value=10, value=4, step=1, key="col_count")
        col_heights = []
        for i in range(int(col_count)):
            col_heights.append(st.number_input(f"Column {i+1} Height (m)", value=3.0, step=0.5, key=f"col_h_{i}"))
        st.subheader("🔧 Refinement Options")
        add_beams = st.checkbox("Add Intermediate Beams", key="add_beams")
        adjust_apex = st.checkbox("Adjust Apex Position", key="adjust_apex")
        submitted = st.form_submit_button("🔄 Apply Refinements", type="primary")
        if submitted:
            if st.session_state.design_brief:
                st.session_state.design_brief['parameters']['A'] = A_new
                st.session_state.design_brief['parameters']['B'] = B_new
                st.session_state.design_brief['parameters']['LAA'] = LAA_new
                st.session_state.design_brief['columns'] = {'count': col_count, 'heights': col_heights}
                st.session_state.design_brief['refinements'] = {'add_beams': add_beams, 'adjust_apex': adjust_apex}
            else:
                st.session_state.design_parameters['A'] = A_new
                st.session_state.design_parameters['B'] = B_new
                st.session_state.design_parameters['LAA'] = LAA_new
            save_design_state(st.session_state.project_id)
            st.success("✅ Refinements applied!")
            st.session_state.stage = 2.9
            st.rerun()
    st.warning("⚠️ Refinements will regenerate the 3D model with new parameters.")

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
            st.session_state.stage = 2.9
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
        st.info("🎉 Your design is now frozen and ready for Stage 2: Structural Testing.")
        if st.button("🔄 Start New Project"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("🧬 Knowledge may evolve. 🌱 Identity shall remain.")
st.caption("SDS Chamber 002 – Tensile Membrane Design Portal (Phase 1.1 POC)")
