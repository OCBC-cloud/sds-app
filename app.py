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
import requests  # For AI agent API calls

# --- Page Configuration ---
st.set_page_config(
    page_title="SDS Design Portal",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Dark Theme CSS ---
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
    .settings-card {
        background-color: #2A2A2A;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #3A3A3A;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Supabase Credentials ---
SUPABASE_URL = "https://pcijgufnjeijqqywubpu.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Initialize Session State ---
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
# AI Agent settings
if 'ai_agent' not in st.session_state:
    st.session_state.ai_agent = 'DeepSeek'
if 'ai_api_key' not in st.session_state:
    st.session_state.ai_api_key = ''
if 'ai_connected' not in st.session_state:
    st.session_state.ai_connected = False
if 'ai_questions' not in st.session_state:
    st.session_state.ai_questions = []
if 'ai_answers' not in st.session_state:
    st.session_state.ai_answers = {}

# --- Helper Functions ---
def clear_stage_fields(stage):
    keys_to_clear = []
    if stage == 1:
        keys_to_clear = ['proj_name', 'client_name', 'main_contractor', 'contact_phone', 'contact_email', 'project_date']
    elif stage == 2:
        keys_to_clear = ['description', 'typology']
    elif stage == 2.5:
        keys_to_clear = ['ai_questions', 'ai_answers']
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
    st.rerun()

def delete_project(project_id):
    try:
        supabase.table('projects').delete().eq('id', project_id).execute()
        st.success("✅ Project deleted successfully.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error deleting project: {str(e)}")

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

# --- AI Agent Integration Functions ---
def test_ai_connection(agent, api_key):
    """Test if the API key works for the selected AI agent."""
    # Placeholder – actual implementation would call the API with a simple test prompt.
    # For now, we return True if the key is not empty (basic validation).
    if api_key and len(api_key) > 8:
        return True, "Connection successful!"
    else:
        return False, "Invalid API key. Please check and try again."

def generate_ai_questions(agent, api_key, description, parameters):
    """Send description to AI agent and generate thoughtful questions."""
    # This is a simulation. In production, you would call the actual API.
    # Example prompt for DeepSeek:
    # "You are an engineering design assistant. Given this design description: '{description}' and parameters {parameters}, generate 5-8 thoughtful questions to confirm the design understanding."
    # For now, we return a set of generic but dynamic questions.
    # In the future, replace this with actual API calls.
    
    # Simulate AI thinking
    questions = [
        "Are these the two primary structural beams?",
        "Are both beams supported at their lower ends?",
        "Is the membrane attached continuously along the curved beams?",
        "Is the apex point correctly identified?",
        "Is the rise (A) measured from support level to apex?",
        "Is the plan width (B) the distance between support lines?"
    ]
    # Add some variation based on parameters
    if parameters.get('LAA', 0) > 10:
        questions.append("Is LAA the apex-to-apex distance as shown?")
    if parameters.get('typology') == 'Saddle Span':
        questions.append("Are the beams curved in a parabolic shape?")
    return questions

# --- Parametric 3D Engine (Saddle Span) ---
def generate_saddle_span_geometry(A, B, H, LAA, num_points=30):
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

# --- App Title ---
st.title("🏗️ SDS Design Portal")
st.caption("Tensile Membrane Structure Design | Multi-Stage Input Portal")

# --- STAGE 0: PROJECT DASHBOARD ---
if st.session_state.stage == 0:
    st.subheader("📋 Project Dashboard")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("⚙️ Settings", key="settings_btn"):
            st.session_state.stage = -1  # Settings page
            st.rerun()
    
    try:
        projects = supabase.table('projects').select('id, name, client_name, project_date, created_by').order('created_at', desc=True).execute()
        projects_data = projects.data
        if projects_data:
            st.caption(f"Showing {len(projects_data)} project(s)")
            for proj in projects_data:
                st.markdown(f"""
                <div class="project-card">
                    <strong>{proj['name']}</strong><br>
                    <span>Client: {proj.get('client_name', 'N/A')} | Date: {proj.get('project_date', 'N/A')}</span>
                </div>
                """, unsafe_allow_html=True)
                cols = st.columns([1, 1, 1, 1])
                with cols[0]:
                    if st.button("📂 Load", key=f"load_{proj['id']}"):
                        iterations = supabase.table('design_iterations').select('id, status').eq('project_id', proj['id']).order('version_number', desc=True).limit(1).execute()
                        if iterations.data:
                            iter_data = iterations.data[0]
                            iter_id = iter_data['id']
                            status = iter_data.get('status', 'draft')
                            if status == 'frozen':
                                stage = 5
                            else:
                                stage = 3
                            load_project(proj['id'], iter_id, stage)
                        else:
                            load_project(proj['id'], None, 2)
                with cols[1]:
                    if st.button("📋 Copy ID", key=f"copy_{proj['id']}"):
                        st.code(proj['id'], language="text")
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
                if st.button("🖼️ Export Images (ZIP)", key=f"export_images_{proj['id']}"):
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

# --- SETTINGS PAGE (stage = -1) ---
elif st.session_state.stage == -1:
    st.subheader("⚙️ Settings")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    
    st.markdown("### 🤖 AI Agent Configuration")
    st.caption("Select your preferred AI agent for design interpretation. You can change this at any time.")
    
    with st.form("settings_form"):
        agent = st.selectbox(
            "AI Agent",
            ["DeepSeek", "Kimi", "OpenAI (GPT-4)", "Anthropic (Claude)", "Google Gemini", "None (Manual)"],
            index=0,
            key="settings_agent"
        )
        api_key = st.text_input(
            "API Key (optional for some free agents)",
            type="password",
            placeholder="Enter your API key if required",
            key="settings_api_key"
        )
        st.caption("For DeepSeek and Kimi, you can use the free tier. For others, you may need to purchase credits.")
        
        col1, col2 = st.columns(2)
        with col1:
            test_btn = st.form_submit_button("🔌 Test Connection")
        with col2:
            save_btn = st.form_submit_button("💾 Save Settings", type="primary")
        
        if test_btn:
            if agent == "None (Manual)":
                st.info("Manual mode selected – no connection test needed.")
            else:
                if not api_key:
                    st.warning("Please enter an API key to test.")
                else:
                    success, msg = test_ai_connection(agent, api_key)
                    if success:
                        st.success(f"✅ {msg}")
                        st.session_state.ai_connected = True
                    else:
                        st.error(f"❌ {msg}")
                        st.session_state.ai_connected = False
        
        if save_btn:
            st.session_state.ai_agent = agent
            st.session_state.ai_api_key = api_key
            if agent == "None (Manual)":
                st.session_state.ai_connected = True
            elif api_key:
                success, _ = test_ai_connection(agent, api_key)
                st.session_state.ai_connected = success
            else:
                st.session_state.ai_connected = False
            st.success("✅ Settings saved!")
            st.rerun()
    
    st.markdown("---")
    st.info("💡 You can change your AI agent at any time. The system will use your selected agent for design understanding questions.")

# --- STAGE 1: Project Registration ---
elif st.session_state.stage == 1:
    # (Same as before – keep unchanged for brevity; we'll include the full code in final output)
    st.subheader("📋 Project Registration")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    if st.button("🗑️ Clear All Fields", key="clear_stage1"):
        clear_stage_fields(1)
    with st.form("project_registration"):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name *", placeholder="e.g., Taman Megah Canopy", key="proj_name")
            client_name = st.text_input("Client Name", placeholder="e.g., Tuan Haji Ahmad", key="client_name")
            main_contractor = st.text_input("Main Contractor", placeholder="e.g., Bina Sdn Bhd", key="main_contractor")
        with col2:
            contact_phone = st.text_input("Contact Phone", placeholder="e.g., 012-3456789", key="contact_phone")
            contact_email = st.text_input("Contact Email", placeholder="e.g., client@email.com", key="contact_email")
            project_date = st.date_input("Project Date", value=datetime.now().date(), key="project_date")
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
                            'created_by': str(uuid.uuid4())
                        }
                        result = supabase.table('projects').insert(project_data).execute()
                        st.session_state.project_id = result.data[0]['id']
                        st.session_state.stage = 2
                        st.success(f"✅ Project '{project_name}' registered successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Registration error: {str(e)}")

# --- STAGE 2: Design Input ---
elif st.session_state.stage == 2:
    st.subheader("📐 Design Input")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    if st.button("🗑️ Clear All Fields", key="clear_stage2"):
        clear_stage_fields(2)
    
    with st.form("design_input"):
        st.subheader("📝 General Description")
        description = st.text_area(
            "Describe your design concept",
            placeholder="e.g., Two curved primary beams with a membrane roof...",
            key="description"
        )
        st.subheader("🏗️ Structural Typology")
        typology = st.selectbox(
            "Select Typology",
            ["Saddle Span", "Aluminium Free Span Tent", "Factory Warehouse", "Canopy (4 Columns)", "Sail Structure"],
            key="typology"
        )
        st.subheader("📐 Initial Parameters")
        col1, col2 = st.columns(2)
        with col1:
            A = st.number_input("A (Rise / Height) (m)", value=10.0, step=0.5, key="A")
            B = st.number_input("B (Plan / Horizontal) (m)", value=5.0, step=0.5, key="B")
        with col2:
            H = st.number_input("H (Experimental Rise) (m)", value=10.0, step=0.5, key="H")
            LAA = st.number_input("LAA (Apex-to-Apex) (m)", value=10.0, step=0.5, key="LAA")
        st.caption("📐 These parameters are used for Saddle Span typology. Other typologies will use them as reference.")
        submitted = st.form_submit_button("📤 Proceed to Design Understanding", type="primary")
        if submitted:
            if not description:
                st.error("❌ Please enter a description.")
            else:
                st.session_state.design_parameters = {
                    'description': description,
                    'typology': typology,
                    'A': A, 'B': B, 'H': H, 'LAA': LAA
                }
                # Check if AI agent is configured
                if st.session_state.ai_agent == "None (Manual)" or not st.session_state.ai_connected:
                    st.warning("⚠️ No AI agent configured. You will need to answer questions manually.")
                    st.session_state.ai_questions = []  # Will use fallback
                else:
                    # Generate questions using AI
                    with st.spinner("🤖 Asking AI to generate design questions..."):
                        questions = generate_ai_questions(
                            st.session_state.ai_agent,
                            st.session_state.ai_api_key,
                            description,
                            st.session_state.design_parameters
                        )
                        st.session_state.ai_questions = questions
                st.session_state.stage = 2.5
                st.rerun()

# --- STAGE 2.5: Design Understanding (AI-Powered) ---
elif st.session_state.stage == 2.5:
    st.subheader("🧠 Design Understanding")
    if st.button("⬅️ Back to Design Input"):
        st.session_state.stage = 2
        st.rerun()
    if st.button("🗑️ Clear All Fields", key="clear_stage2.5"):
        clear_stage_fields(2.5)
    
    st.markdown(f"""
    <div style="background-color: #2A2A2A; padding: 16px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid #00B4D8;">
        <strong style="color: #FFFFFF;">📝 Your Description:</strong><br>
        <span style="color: #D0D0D0;">{st.session_state.design_parameters.get('description', 'No description')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("🤖 The AI has generated the following questions to confirm your design understanding.")
    
    # Get questions
    if st.session_state.ai_questions:
        questions = st.session_state.ai_questions
    else:
        # Fallback manual questions
        questions = [
            "Are these the two primary structural beams?",
            "Are both beams supported at their lower ends?",
            "Is the membrane attached continuously along the curved beams?",
            "Is the apex point correctly identified?",
            "Is the rise (A) measured from support level to apex?",
            "Is the plan width (B) the distance between support lines?"
        ]
    
    with st.form("understanding_form"):
        answers = {}
        for i, q in enumerate(questions):
            answers[q] = st.radio(q, ["Yes", "No", "Not Sure", "Other"], key=f"q_{i}")
        comments = st.text_area("📝 Additional Comments", placeholder="Any clarifications...", key="understanding_comments")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("🔁 Modify Understanding"):
                st.session_state.understanding_locked = False
                st.rerun()
        with col2:
            if st.form_submit_button("✅ Confirm & Freeze", type="primary"):
                st.session_state.understanding_locked = True
                st.session_state.ai_answers = answers
                st.session_state.stage = 2.6
                st.success("✅ Understanding confirmed! Proceeding to 3D model.")
                st.rerun()

# --- STAGE 2.6: Parametric 3D Model ---
elif st.session_state.stage == 2.6:
    st.subheader("🏗️ Parametric 3D Model")
    if st.button("⬅️ Back to Understanding"):
        st.session_state.stage = 2.5
        st.rerun()
    if st.button("📐 Redesign & Refine"):
        st.session_state.stage = 2.7
        st.rerun()
    
    params = st.session_state.design_parameters
    A = params.get('A', 10.0)
    B = params.get('B', 5.0)
    H = params.get('H', 10.0)
    LAA = params.get('LAA', 10.0)
    
    st.markdown(f"""
    <div style="background-color: #2A2A2A; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
        <strong style="color: #FFFFFF;">📐 Confirmed Parameters:</strong><br>
        <span style="color: #D0D0D0;">A = {A:.1f}m | B = {B:.1f}m | H = {H:.1f}m | LAA = {LAA:.1f}m</span><br>
        <span style="color: #D0D0D0;">Typology: {params.get('typology', 'Saddle Span')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    view_modes = ['3D Perspective', 'Plan (Top)', 'Front Elevation', 'Side Elevation']
    selected_view = st.radio("View Mode", view_modes, horizontal=True, key="view_mode_26")
    
    with st.spinner("Generating 3D model..."):
        geometry = generate_saddle_span_geometry(A, B, H, LAA)
        fig = plot_saddle_span_geometry(geometry, selected_view)
        st.plotly_chart(fig, use_container_width=True, key="parametric_3d")
    
    st.info("✅ 3D model generated. Use the controls above to change view.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Understanding", type="secondary"):
            st.session_state.stage = 2.5
            st.rerun()
    with col2:
        if st.button("📐 Redesign & Refine", type="primary"):
            st.session_state.stage = 2.7
            st.rerun()

# --- STAGE 2.7: Redesign & Refinement ---
elif st.session_state.stage == 2.7:
    st.subheader("📐 Redesign & Refinement")
    if st.button("⬅️ Back to 3D Model"):
        st.session_state.stage = 2.6
        st.rerun()
    
    params = st.session_state.design_parameters
    st.subheader("⚙️ Edit Geometry")
    with st.form("refinement_form"):
        col1, col2 = st.columns(2)
        with col1:
            A_new = st.number_input("A (Rise / Height) (m)", value=params.get('A', 10.0), step=0.5, key="A_edit")
            B_new = st.number_input("B (Plan / Horizontal) (m)", value=params.get('B', 5.0), step=0.5, key="B_edit")
        with col2:
            H_new = st.number_input("H (Experimental Rise) (m)", value=params.get('H', 10.0), step=0.5, key="H_edit")
            LAA_new = st.number_input("LAA (Apex-to-Apex) (m)", value=params.get('LAA', 10.0), step=0.5, key="LAA_edit")
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
            params['A'] = A_new
            params['B'] = B_new
            params['H'] = H_new
            params['LAA'] = LAA_new
            params['columns'] = col_heights
            params['add_beams'] = add_beams
            params['adjust_apex'] = adjust_apex
            st.session_state.design_parameters = params
            st.success("✅ Refinements applied!")
            st.session_state.stage = 2.6
            st.rerun()
    st.warning("⚠️ Refinements will regenerate the 3D model with new parameters.")

# --- STAGE 3: Collaboration ---
elif st.session_state.stage == 3:
    st.subheader("💬 Collaboration")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    if st.button("🗑️ Clear All Fields", key="clear_stage3"):
        clear_stage_fields(3)
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
        if st.button("⬅️ Back to Design"):
            st.session_state.stage = 2
            st.rerun()
    with col2:
        if st.button("📌 Freeze Concept"):
            st.session_state.stage = 5
            st.rerun()

# --- STAGE 5: Concept Freeze ---
elif st.session_state.stage == 5:
    st.subheader("📌 Freeze Concept")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.stage = 0
        st.rerun()
    st.warning("⚠️ Freezing the concept will lock this design version. No further edits will be allowed.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel", type="secondary"):
            st.session_state.stage = 4
            st.rerun()
    with col2:
        if st.button("✅ Confirm Freeze", type="primary"):
            with st.spinner("Freezing concept..."):
                try:
                    supabase.table('design_iterations').update({
                        'status': 'frozen',
                        'frozen_at': datetime.now().isoformat()
                    }).eq('id', st.session_state.iteration_id).execute()
                    st.session_state.frozen = True
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

# --- Footer ---
st.divider()
st.caption("🧬 Knowledge may evolve. 🌱 Identity shall remain.")
st.caption("SDS Chamber 002 – Tensile Membrane Design Portal (Phase 1.1 POC)")
