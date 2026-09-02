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
import os

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
# Custom Dark Theme CSS – High Contrast Labels
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
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []
if 'round' not in st.session_state:
    st.session_state.round = 0
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = ''

# ============================================================================
# Helper Functions
# ============================================================================

def clear_stage_fields(stage):
    keys_to_clear = []
    if stage == 1:
        keys_to_clear = ['proj_name', 'client_name', 'main_contractor', 'contact_phone', 'contact_email', 'project_date']
    elif stage == 2:
        keys_to_clear = ['description', 'uploaded_images']
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
                st.session_state.uploaded_images = state.get('uploaded_images', [])
                st.session_state.round = state.get('round', 0)
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
        'uploaded_images': st.session_state.uploaded_images,
        'round': st.session_state.round,
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
        st.session_state.design_brief = None
        st.session_state.design_brief_confirmed = False
        st.session_state.frozen = False
        st.session_state.ai_bridge_prompt = ''
        st.session_state.ai_bridge_response = ''
        st.session_state.uploaded_images = []
        st.session_state.round = 0
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
# Design Engine (No "AI" References)
# ============================================================================

def call_design_engine(prompt, api_key, images=None):
    """Call the design interpretation engine."""
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": "You are a structural engineering design expert. You MUST output ONLY valid JSON. No explanations, no markdown, just pure JSON."},
        {"role": "user", "content": prompt}
    ]
    
    if images:
        image_text = "\n\n**Uploaded Images:**\n"
        for i, img in enumerate(images):
            image_text += f"- Image {i+1}: {img}\n"
        messages[1]["content"] += image_text
    
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return content, None
        else:
            return None, f"API Error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Request Error: {str(e)}"

def generate_design_prompt(description, images=None):
    """Generate a prompt for the design interpretation engine."""
    prompt = f"""You are an expert structural engineering design consultant.

**Your Task:**
Interpret the user's design description and produce a complete Design Brief in JSON format.

**User's Description:**
{description}

**Instructions:**
1. Extract all design elements from the description:
   - Beams (number, type, curve, positions, height, material)
   - Supports (positions, type)
   - Columns (number, positions, height)
   - Membranes (type, attachments, material)
   - Anchors (positions)

2. Generate a structured JSON Design Brief using the following schema:
{{
  "version": "1.0",
  "project": {{
    "name": "Untitled",
    "description": "User description",
    "images": []
  }},
  "elements": {{
    "beams": [],
    "supports": [],
    "columns": [],
    "membranes": [],
    "anchors": []
  }}
}}

3. For each element, provide all relevant parameters.

4. Use realistic engineering values.

5. OUTPUT ONLY THE JSON OBJECT. NO OTHER TEXT.

Example beam:
{{
  "id": "B1",
  "type": "curved",
  "curve": "parabolic",
  "start": [-7.5, 0, 0],
  "end": [7.5, 0, 0],
  "height": 6.5,
  "material": "Steel",
  "section": "CHS 219 x 6.3"
}}

Example support:
{{
  "position": [-7.5, 0, 0],
  "type": "pinned"
}}

Example membrane:
{{
  "id": "M1",
  "type": "saddle",
  "attachments": ["B1", "B2"],
  "material": "PVC/PTFE",
  "prestress": "3.0 kN/m"
}}
"""
    return prompt

def generate_feedback_prompt(description, design_brief, feedback):
    """Generate a prompt for refining the Design Brief."""
    current_brief = json.dumps(design_brief, indent=2)
    prompt = f"""You are an expert structural engineering design consultant.

**Current Design Brief:**
{current_brief}

**User Feedback:**
{feedback}

**Task:**
Update the Design Brief based on the user's feedback. Modify only the relevant elements. Keep the rest unchanged.

**Instructions:**
1. Read the user's feedback carefully.
2. Identify which elements need to be changed.
3. Update the JSON Design Brief accordingly.
4. Return ONLY the updated JSON object.

**Original Description:**
{description}

OUTPUT ONLY THE JSON OBJECT. NO OTHER TEXT."""
    return prompt

def parse_design_brief(response_text):
    """Extract and parse JSON from response."""
    try:
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            return data, None
        else:
            return None, "No JSON found in response."
    except json.JSONDecodeError as e:
        return None, f"JSON parsing error: {str(e)}"

# ============================================================================
# Universal Geometry Engine
# ============================================================================

def generate_geometry_from_brief(brief):
    """Generate 3D geometry from a Design Brief."""
    geometry = {
        'beams': [],
        'supports': [],
        'columns': [],
        'membranes': [],
        'anchors': []
    }
    
    elements = brief.get('elements', {})
    
    for beam in elements.get('beams', []):
        if beam.get('type') == 'curved' and beam.get('curve') == 'parabolic':
            start = beam.get('start', [-5, 0, 0])
            end = beam.get('end', [5, 0, 0])
            height = beam.get('height', 5.0)
            num_points = 30
            
            x = np.linspace(start[0], end[0], num_points)
            span = end[0] - start[0]
            z = height * (1 - (2 * (x - start[0]) / span)**2) if span != 0 else np.zeros_like(x)
            y = np.full_like(x, start[1])
            
            geometry['beams'].append({
                'id': beam.get('id', 'B1'),
                'x': x.tolist(),
                'y': y.tolist(),
                'z': z.tolist(),
                'material': beam.get('material', 'Steel'),
                'section': beam.get('section', 'CHS 219 x 6.3'),
                'height': height
            })
        elif beam.get('type') == 'curved' and beam.get('curve') == 'path':
            path = beam.get('path', [])
            if len(path) >= 2:
                x = [p[0] for p in path]
                y = [p[1] for p in path]
                z = [p[2] for p in path]
                geometry['beams'].append({
                    'id': beam.get('id', 'B1'),
                    'x': x,
                    'y': y,
                    'z': z,
                    'material': beam.get('material', 'Steel'),
                    'section': beam.get('section', 'CHS 219 x 6.3'),
                    'height': max(z) if z else 0
                })
    
    for support in elements.get('supports', []):
        geometry['supports'].append({
            'position': support.get('position', [0, 0, 0]),
            'type': support.get('type', 'pinned')
        })
    
    for column in elements.get('columns', []):
        geometry['columns'].append({
            'position': column.get('position', [0, 0, 0]),
            'height': column.get('height', 4.0),
            'section': column.get('section', 'CHS 168 x 5.0')
        })
    
    for membrane in elements.get('membranes', []):
        attachments = membrane.get('attachments', [])
        if len(attachments) >= 2:
            beam1_data = None
            beam2_data = None
            for beam in geometry['beams']:
                if beam['id'] == attachments[0]:
                    beam1_data = beam
                if beam['id'] == attachments[1]:
                    beam2_data = beam
            
            if beam1_data and beam2_data:
                x1 = np.array(beam1_data['x'])
                y1 = np.array(beam1_data['y'])
                z1 = np.array(beam1_data['z'])
                x2 = np.array(beam2_data['x'])
                y2 = np.array(beam2_data['y'])
                z2 = np.array(beam2_data['z'])
                
                num_points = len(x1)
                X_surf = np.zeros((num_points, 2))
                Y_surf = np.zeros((num_points, 2))
                Z_surf = np.zeros((num_points, 2))
                
                for i in range(num_points):
                    X_surf[i, 0] = x1[i]
                    X_surf[i, 1] = x2[i]
                    Y_surf[i, 0] = y1[i]
                    Y_surf[i, 1] = y2[i]
                    Z_surf[i, 0] = z1[i]
                    Z_surf[i, 1] = z2[i]
                
                geometry['membranes'].append({
                    'id': membrane.get('id', 'M1'),
                    'surface': (X_surf.tolist(), Y_surf.tolist(), Z_surf.tolist()),
                    'material': membrane.get('material', 'PVC/PTFE'),
                    'prestress': membrane.get('prestress', '3.0 kN/m')
                })
    
    for anchor in elements.get('anchors', []):
        geometry['anchors'].append({
            'position': anchor.get('position', [0, 0, 0]),
            'type': anchor.get('type', 'base plate')
        })
    
    return geometry

def plot_geometry(geometry, view_mode='3D'):
    """Plot the 3D geometry."""
    fig = go.Figure()
    
    for beam in geometry['beams']:
        x = beam['x']
        y = beam['y']
        z = beam['z']
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            line=dict(color='#FF6B6B', width=6),
            name=f"Beam {beam.get('id', '')}"
        ))
    
    for i, support in enumerate(geometry['supports']):
        pos = support['position']
        fig.add_trace(go.Scatter3d(
            x=[pos[0]], y=[pos[1]], z=[pos[2]],
            mode='markers',
            marker=dict(color='#4ECDC4', size=12, symbol='circle'),
            name=f"Support {i+1}"
        ))
    
    for i, column in enumerate(geometry['columns']):
        pos = column['position']
        h = column['height']
        fig.add_trace(go.Scatter3d(
            x=[pos[0], pos[0]],
            y=[pos[1], pos[1]],
            z=[0, h],
            mode='lines',
            line=dict(color='#8B8B8B', width=6),
            name=f"Column {i+1}"
        ))
    
    for i, anchor in enumerate(geometry['anchors']):
        pos = anchor['position']
        fig.add_trace(go.Scatter3d(
            x=[pos[0]], y=[pos[1]], z=[pos[2]],
            mode='markers',
            marker=dict(color='#FFD93D', size=8, symbol='star'),
            name=f"Anchor {i+1}"
        ))
    
    for membrane in geometry['membranes']:
        X_surf, Y_surf, Z_surf = membrane['surface']
        fig.add_trace(go.Surface(
            x=X_surf, y=Y_surf, z=Z_surf,
            colorscale=[[0, '#E8E8E8'], [1, '#F5F5F5']],
            opacity=0.6,
            name=f"Membrane {membrane.get('id', '')}",
            showscale=False,
            lighting=dict(ambient=0.6, diffuse=0.8, specular=0.3)
        ))
    
    if geometry['beams']:
        beam1 = geometry['beams'][0]
        x = np.array(beam1['x'])
        z = np.array(beam1['z'])
        if len(x) > 0 and len(z) > 0:
            mid_idx = len(x) // 2
            fig.add_trace(go.Scatter3d(
                x=[x[0], x[-1]],
                y=[beam1['y'][0], beam1['y'][-1]],
                z=[0, 0],
                mode='lines',
                line=dict(color='#FFD93D', width=2, dash='dash'),
                name='Span'
            ))
            fig.add_trace(go.Scatter3d(
                x=[x[mid_idx]],
                y=[beam1['y'][mid_idx]],
                z=[-0.5],
                mode='text',
                text=[f"Span = {abs(x[-1] - x[0]):.1f}m"],
                textfont=dict(color='#FFD93D', size=12),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[x[mid_idx], x[mid_idx]],
                y=[beam1['y'][mid_idx], beam1['y'][mid_idx]],
                z=[0, z[mid_idx]],
                mode='lines',
                line=dict(color='#FFD93D', width=2, dash='dash'),
                name='Height'
            ))
            fig.add_trace(go.Scatter3d(
                x=[x[mid_idx] + 0.5],
                y=[beam1['y'][mid_idx] + 0.5],
                z=[z[mid_idx]/2],
                mode='text',
                text=[f"H = {z[mid_idx]:.1f}m"],
                textfont=dict(color='#FFD93D', size=12),
                showlegend=False
            ))
    
    scene_config = dict(
        bgcolor='#1E1E1E',
        xaxis=dict(title='Length (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        yaxis=dict(title='Width (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        zaxis=dict(title='Height (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
        aspectmode='manual',
        aspectratio=dict(x=1.5, y=0.8, z=1.0)
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
    st.caption("Structural Design | Upload, Describe, Review, Refine")
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
                    st.session_state.design_brief = state.get('design_brief', None)
                    st.session_state.design_brief_confirmed = state.get('confirmed', False)
                    st.session_state.frozen = state.get('frozen', False)
                    st.session_state.ai_bridge_prompt = state.get('ai_prompt', '')
                    st.session_state.uploaded_images = state.get('uploaded_images', [])
                    st.session_state.round = state.get('round', 0)
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
            st.session_state.design_brief = None
            st.session_state.design_brief_confirmed = False
            st.session_state.frozen = False
            st.session_state.ai_bridge_prompt = ''
            st.session_state.ai_bridge_response = ''
            st.session_state.uploaded_images = []
            st.session_state.round = 0
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
        current_state.get('design_brief'),
        current_state.get('feedback_history', []),
        current_state.get('ai_prompt'),
        current_state.get('iteration_count', 0) > 0
    ])
    if has_data:
        with st.form("load_selective"):
            keep_description = st.checkbox("📝 Description", value=True, key="keep_description")
            keep_design_brief = st.checkbox("📋 Design Brief", value=True, key="keep_design_brief")
            keep_feedback = st.checkbox("📝 Feedback History", value=True, key="keep_feedback")
            keep_images = st.checkbox("🖼️ Uploaded Images", value=True, key="keep_images")
            if st.form_submit_button("✅ Load Selected", type="primary"):
                new_state = {}
                if keep_description:
                    new_state['parameters'] = current_state.get('parameters', {})
                if keep_design_brief and current_state.get('design_brief'):
                    new_state['design_brief'] = current_state['design_brief']
                    new_state['confirmed'] = True
                if keep_feedback and current_state.get('feedback_history'):
                    new_state['feedback_history'] = current_state['feedback_history']
                if keep_images and current_state.get('uploaded_images'):
                    new_state['uploaded_images'] = current_state['uploaded_images']
                new_state['iteration_count'] = current_state.get('iteration_count', 0)
                new_state['frozen'] = current_state.get('frozen', False)
                new_state['round'] = current_state.get('round', 0)
                supabase.table('projects').update({'design_state': new_state}).eq('id', project_id).execute()
                st.session_state.project_id = project_id
                st.session_state.design_parameters = new_state.get('parameters', {})
                st.session_state.iteration_count = new_state.get('iteration_count', 0)
                st.session_state.feedback_history = new_state.get('feedback_history', [])
                st.session_state.design_brief = new_state.get('design_brief', None)
                st.session_state.design_brief_confirmed = new_state.get('confirmed', False)
                st.session_state.frozen = new_state.get('frozen', False)
                st.session_state.ai_bridge_prompt = new_state.get('ai_prompt', '')
                st.session_state.uploaded_images = new_state.get('uploaded_images', [])
                st.session_state.round = new_state.get('round', 0)
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
        <span style="color: #D0D0D0;">1. Upload images (sketches, photos, GPS images) → 2. Describe your design → 3. Generate Design Brief → 4. Review 3D model → 5. Refine until satisfied</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("design_input"):
        st.subheader("🖼️ Upload Images")
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
            placeholder="e.g., A saddle span tensile membrane structure covering a community gathering space. Two curved primary beams with a PVC/PTFE membrane roof. The structure spans 15 meters with a rise of 6.5 meters. The beams are parallel with separate apexes, and the membrane is attached continuously along the curved beams. Supports are pinned at the base.",
            key="description",
            height=200,
            value=st.session_state.design_parameters.get('description', '')
        )
        
        st.caption("💡 Be as detailed as possible. Include dimensions, materials, and structural elements.")
        
        submitted = st.form_submit_button("🚀 Generate Design Brief", type="primary")
        if submitted:
            if not description:
                st.error("❌ Please describe your design.")
            else:
                st.session_state.design_parameters = {
                    'description': description
                }
                st.session_state.ai_bridge_prompt = generate_design_prompt(description, st.session_state.uploaded_images)
                st.session_state.iteration_count = 0
                st.session_state.feedback_history = []
                st.session_state.design_brief = None
                st.session_state.design_brief_confirmed = False
                st.session_state.round = 0
                save_design_state(st.session_state.project_id)
                save_project_metadata(st.session_state.project_id)
                st.session_state.stage = 2.5
                st.rerun()

# ============================================================================
# STAGE 2.5: DESIGN INTERPRETATION
# ============================================================================

elif st.session_state.stage == 2.5:
    st.subheader("🧠 Design Interpretation")
    if st.button("⬅️ Back to Design Input"):
        st.session_state.stage = 2
        st.rerun()
    
    st.markdown(f"""
    <div style="background-color: #2A2A2A; padding: 16px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid #00B4D8;">
        <strong style="color: #FFFFFF;">📝 Your Description:</strong><br>
        <span style="color: #D0D0D0;">{st.session_state.design_parameters.get('description', 'No description')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🤖 Design Interpretation")
    st.caption("The system will interpret your description and images to generate a Design Brief.")
    st.info(f"🔄 Round {st.session_state.round + 1}")
    
    if st.session_state.feedback_history:
        st.markdown("**📋 Feedback History:**")
        for i, fb in enumerate(st.session_state.feedback_history):
            st.caption(f"Round {i+1}: {fb[:100]}...")
    
    prompt = st.session_state.ai_bridge_prompt
    with st.expander("📋 View Prompt (Advanced)"):
        st.text_area("Design Prompt", prompt, height=200, key="ai_prompt_display")
    
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
        has_api_key = True
    except:
        has_api_key = False
        st.warning("⚠️ Design engine key not found. Use the manual fallback below.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚀 Generate Design Brief", type="primary"):
            if has_api_key:
                with st.spinner("🔄 Processing your design..."):
                    result, error = call_design_engine(prompt, api_key, st.session_state.uploaded_images)
                    if result:
                        st.success("✅ Design Brief received!")
                        data, parse_error = parse_design_brief(result)
                        if data:
                            st.session_state.design_brief = data
                            st.session_state.design_brief_confirmed = False
                            st.session_state.iteration_count += 1
                            st.session_state.round += 1
                            save_design_state(st.session_state.project_id)
                            st.success("✅ Design Brief extracted successfully! Proceeding to 3D model.")
                            st.session_state.stage = 3.0
                            st.rerun()
                        else:
                            st.error(f"❌ Error parsing Design Brief: {parse_error}")
                            st.text_area("Raw Response (for debugging)", result, height=150)
                    else:
                        st.error(f"❌ Interpretation Error: {error}")
                        st.info("💡 You can use the manual fallback below.")
            else:
                st.error("❌ No design engine key found.")
    
    with col2:
        if st.button("📝 Manual Fallback", type="secondary"):
            st.session_state.stage = 2.6
            st.rerun()

# ============================================================================
# STAGE 2.6: MANUAL FALLBACK (with Prompt Generation)
# ============================================================================

elif st.session_state.stage == 2.6:
    st.subheader("📝 Manual Design Brief")
    if st.button("⬅️ Back to Design Interpretation"):
        st.session_state.stage = 2.5
        st.rerun()
    
    # --- FORCE prompt regeneration from description and images ---
    description = st.session_state.design_parameters.get('description', '')
    images = st.session_state.uploaded_images
    st.session_state.ai_bridge_prompt = generate_design_prompt(description, images)
    
    st.markdown("""
    <div style="background-color: #2A3A4A; padding: 16px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid #00B4D8;">
        <strong style="color: #FFFFFF;">📋 How It Works</strong><br>
        <span style="color: #D0D0D0;">1. Copy the prompt below → 2. Paste it into your design tool → 3. Copy the response → 4. Paste it back here</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 1: Copy Prompt
    st.markdown("### 📋 Step 1: Copy the Prompt")
    prompt = st.session_state.ai_bridge_prompt
    st.text_area("Design Prompt (Copy this to your design tool)", prompt, height=300, key="ai_prompt_fallback", disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Copy Prompt", key="copy_prompt_fallback"):
            st.code(prompt, language="text")
            st.caption("✅ Prompt copied! You can highlight and copy from the box above.")
    
    st.markdown("---")
    
    # Step 2: Paste Response
    st.markdown("### 📋 Step 2: Paste the Design Brief")
    st.caption("After your design tool returns the JSON response, paste it below.")
    
    response = st.text_area(
        "Design Brief Response (JSON)",
        placeholder="Paste the JSON response here...",
        height=200,
        key="ai_response_fallback"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Copy Design Brief", key="copy_response"):
            if response:
                st.code(response, language="json")
                st.caption("✅ Design Brief copied! You can highlight and copy from the box above.")
            else:
                st.warning("⚠️ No response to copy. Please paste the JSON first.")
    
    with col2:
        if st.button("📋 Paste Response", key="paste_response"):
            st.markdown("""
            <script>
            navigator.clipboard.readText().then(text => {
                const textareas = document.querySelectorAll('textarea');
                for (let textarea of textareas) {
                    if (textarea.placeholder && textarea.placeholder.includes('Paste the JSON response here')) {
                        textarea.value = text;
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        break;
                    }
                }
            }).catch(err => {
                alert('Could not paste from clipboard. Please paste manually.');
            });
            </script>
            """, unsafe_allow_html=True)
            st.caption("✅ Paste attempt triggered. If it doesn't work, please paste manually (Ctrl+V / Cmd+V).")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Process Design Brief", type="primary"):
            if response:
                data, error = parse_design_brief(response)
                if data:
                    st.session_state.design_brief = data
                    st.session_state.design_brief_confirmed = False
                    st.session_state.iteration_count += 1
                    st.session_state.round += 1
                    save_design_state(st.session_state.project_id)
                    st.success("✅ Design Brief extracted successfully!")
                    st.session_state.stage = 3.0
                    st.rerun()
                else:
                    st.error(f"❌ Error parsing Design Brief: {error}")
                    st.info("💡 Please ensure the response is valid JSON.")
            else:
                st.error("❌ Please paste the design brief response first.")
    
    with col2:
        if st.button("💾 Save Progress", type="secondary"):
            save_design_state(st.session_state.project_id)
            st.success("✅ Progress saved!")
    
    st.markdown("---")
    st.caption("💡 If you need a reference, here is the expected JSON structure:")
    with st.expander("📋 JSON Structure Reference"):
        st.code("""
{
  "version": "1.0",
  "project": {
    "name": "Project Name",
    "description": "Design description",
    "images": []
  },
  "elements": {
    "beams": [
      {
        "id": "B1",
        "type": "curved",
        "curve": "parabolic",
        "path": [[-10, 0, 0], [0, 0, 6], [10, 0, 0]],
        "material": "Steel",
        "section": "CHS 219 x 6.3",
        "finish": "Galvanized"
      }
    ],
    "supports": [
      {"position": [-10, 0, 0], "type": "pinned"}
    ],
    "columns": [],
    "membranes": [
      {
        "id": "M1",
        "type": "saddle",
        "attachments": ["B1", "B2"],
        "material": "PVC-coated polyester",
        "thickness": "0.8 mm",
        "prestress": "3.0 kN/m"
      }
    ],
    "anchors": [
      {"position": [-10, 0, 0], "type": "base plate with 4 bolts"}
    ]
  }
}
        """, language="json")

# ============================================================================
# STAGE 3.0: 3D MODEL + REFINEMENT
# ============================================================================

elif st.session_state.stage == 3.0:
    st.subheader("🏗️ 3D Design Model")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    if st.button("💾 Save Progress", key="save_progress_3"):
        save_design_state(st.session_state.project_id)
        st.success("✅ Progress saved!")
    
    if st.session_state.design_brief:
        with st.expander("📋 View Design Brief"):
            st.json(st.session_state.design_brief)
        
        try:
            geometry = generate_geometry_from_brief(st.session_state.design_brief)
            
            view_modes = ['3D Perspective', 'Plan (Top)', 'Front Elevation', 'Side Elevation']
            selected_view = st.radio("View Mode", view_modes, horizontal=True, key="view_mode_3")
            
            current_inputs = (str(st.session_state.design_brief), selected_view)
            
            rebuild_needed = (
                st.session_state.cached_fig is None or
                st.session_state.cached_inputs != current_inputs
            )
            
            if rebuild_needed:
                with st.spinner("🔄 Building 3D model..."):
                    fig = plot_geometry(geometry, selected_view)
                    st.session_state.cached_fig = fig
                    st.session_state.cached_inputs = current_inputs
            else:
                fig = st.session_state.cached_fig
            
            st.plotly_chart(fig, use_container_width=True, key="universal_3d")
            
            st.subheader("📋 Design Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Beams", len(geometry['beams']))
            with col2:
                st.metric("Supports", len(geometry['supports']))
            with col3:
                st.metric("Columns", len(geometry['columns']))
            
            if geometry['membranes']:
                st.info(f"🟦 Membranes: {len(geometry['membranes'])}")
            
            st.markdown("---")
            st.subheader("🔄 Refine Design")
            st.caption(f"Round {st.session_state.round}. Provide feedback to improve the design.")
            
            feedback = st.text_area(
                "Your Feedback",
                placeholder="e.g., Change the beam material to aluminium. Add two more columns. The membrane should be attached differently.",
                height=100,
                key="refinement_feedback"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refine Design", type="primary"):
                    if feedback:
                        st.session_state.user_feedback = feedback
                        st.session_state.feedback_history.append(feedback)
                        
                        updated_prompt = generate_feedback_prompt(
                            st.session_state.design_parameters.get('description', ''),
                            st.session_state.design_brief,
                            feedback
                        )
                        st.session_state.ai_bridge_prompt = updated_prompt
                        st.session_state.stage = 2.5
                        st.rerun()
                    else:
                        st.error("❌ Please enter feedback.")
            
            with col2:
                if st.button("✅ Accept Design", type="secondary"):
                    st.session_state.design_brief_confirmed = True
                    save_design_state(st.session_state.project_id)
                    st.success("✅ Design accepted! Proceeding to collaboration.")
                    st.session_state.stage = 3
                    st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating 3D model: {str(e)}")
            st.info("💡 Please go back to Design Interpretation and regenerate the Design Brief.")
            if st.button("⬅️ Back to Design Interpretation"):
                st.session_state.stage = 2.5
                st.rerun()
    else:
        st.warning("No Design Brief found. Please go back to Design Interpretation.")
        if st.button("⬅️ Back to Design Interpretation"):
            st.session_state.stage = 2.5
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
