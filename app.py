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

# --- Page Configuration ---
st.set_page_config(
    page_title="SDS Design Portal",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Dark Theme CSS (Higher Contrast) ---
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #1E1E1E;
    }
    /* Sidebar */
    .css-1d391kg {
        background-color: #2A2A2A;
    }
    /* Labels - NOW WHITE for better readability */
    .stTextInput label, .stTextArea label, .stNumberInput label, .stSelectbox label, .stDateInput label {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    /* Input fields - LIGHTER BACKGROUND */
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #3A3A3A !important;
        color: #FFFFFF !important;
        border: 1px solid #5A5A5A !important;
        border-radius: 8px !important;
    }
    /* Placeholders */
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #B0B0B0 !important;
    }
    /* Dropdowns */
    .stSelectbox select {
        background-color: #3A3A3A !important;
        color: #FFFFFF !important;
        border: 1px solid #5A5A5A !important;
        border-radius: 8px !important;
    }
    /* Buttons */
    .stButton button {
        background-color: #00B4D8 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .stButton button:hover {
        background-color: #0090B0 !important;
    }
    /* Headers */
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
    }
    /* Captions and text */
    .stCaption, .stMarkdown p {
        color: #D0D0D0 !important;
    }
    /* Success, Error, Info */
    .stAlert {
        background-color: #2A3A2A !important;
        border-color: #52B788 !important;
        color: #D4EDDA !important;
    }
    .stError {
        background-color: #3A2A2A !important;
        border-color: #E63946 !important;
        color: #F8D7DA !important;
    }
    .stInfo {
        background-color: #2A3A4A !important;
        border-color: #00B4D8 !important;
        color: #D4EDF4 !important;
    }
    .stWarning {
        background-color: #4A3A2A !important;
        border-color: #F4A261 !important;
        color: #FFF3E0 !important;
    }
    hr {
        border-color: #3A3A3A !important;
    }
    .stProgress > div > div {
        background-color: #00B4D8 !important;
    }
    /* Metric labels and values */
    div[data-testid="metric-container"] label {
        color: #FFFFFF !important;
    }
    div[data-testid="metric-container"] div {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Supabase Credentials ---
SUPABASE_URL = "https://pcijgufnjeijqqywubpu.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Initialize Session State ---
if 'stage' not in st.session_state:
    st.session_state.stage = 1
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

# --- App Title ---
st.title("🏗️ SDS Design Portal")
st.caption("Tensile Membrane Structure Design | Multi-Stage Input Portal")

# --- Stage Navigation ---
stages = ["1. Project Registration", "2. Design Input", "3. Collaboration", "4. 3D View", "5. Concept Freeze"]
current_stage = st.session_state.stage - 1
st.progress((current_stage + 1) / len(stages))
st.caption(f"Stage {st.session_state.stage} of {len(stages)}: {stages[current_stage]}")

# --- Helper: Clear all fields for current stage ---
def clear_stage_fields(stage):
    keys_to_clear = []
    if stage == 1:
        keys_to_clear = ['proj_name', 'client_name', 'main_contractor', 'contact_phone', 'contact_email', 'project_date']
    elif stage == 2:
        keys_to_clear = ['description', 'width', 'depth', 'length', 'height', 'structure_type', 'roof_type', 'design_images']
    elif stage == 3:
        keys_to_clear = ['stakeholder', 'message']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- Stage 1: Project Registration ---
if st.session_state.stage == 1:
    st.subheader("📋 Project Registration")
    
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

# --- Stage 2: Design Input ---
elif st.session_state.stage == 2:
    st.subheader("📐 Design Input")
    
    if st.button("🗑️ Clear All Fields", key="clear_stage2"):
        clear_stage_fields(2)
    
    with st.form("design_input"):
        col1, col2 = st.columns(2)
        with col1:
            description = st.text_area("General Description", placeholder="Describe the design concept, site context, and key requirements...", key="description")
            width = st.number_input("Width (m)", value=0.0, step=0.1, key="width")
            depth = st.number_input("Depth (m)", value=0.0, step=0.1, key="depth")
        with col2:
            length = st.number_input("Length (m)", value=0.0, step=0.1, key="length")
            height = st.number_input("Height (m)", value=0.0, step=0.1, key="height")
            structure_type = st.selectbox("Structure Type", ["Steel", "Aluminium", "Timber", "Other"], key="structure_type")
            roof_type = st.selectbox("Roof Type", ["Tensile Fabric (PVC/PTFE)", "ETFE Cushion", "Other"], key="roof_type")
        
        st.subheader("🖼️ Upload Images")
        uploaded_files = st.file_uploader(
            "Choose images (JPG/PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="design_images",
            help="Upload sketches, photos of existing structures, or site inspiration"
        )
        # Removed the "Clear Images" button to avoid Streamlit form button conflict.
        
        st.subheader("✏️ Sketch Board")
        st.info("📝 Sketch board feature coming soon. For now, upload images above.")
        
        submitted = st.form_submit_button("💾 Save Design", type="primary")
        
        if submitted:
            with st.spinner("Saving design..."):
                try:
                    iteration_data = {
                        'project_id': st.session_state.project_id,
                        'version_number': 1,
                        'material': structure_type,
                        'standard': "MS (EN)",
                        'description': description if description else None,
                        'width': width if width > 0 else None,
                        'depth': depth if depth > 0 else None,
                        'length': length if length > 0 else None,
                        'height': height if height > 0 else None,
                        'structure_type': structure_type,
                        'roof_type': roof_type,
                        'status': 'draft',
                        'uploaded_by': str(uuid.uuid4())
                    }
                    result = supabase.table('design_iterations').insert(iteration_data).execute()
                    st.session_state.iteration_id = result.data[0]['id']
                    
                    if uploaded_files:
                        for img in uploaded_files:
                            image_data = img.read()
                            file_path = f"projects/{st.session_state.project_id}/{st.session_state.iteration_id}/{img.name}"
                            supabase.storage.from_('design-uploads').upload(file_path, image_data)
                    
                    st.success("✅ Design saved successfully!")
                    st.session_state.stage = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving design: {str(e)}")

# --- Stage 3: Collaboration ---
elif st.session_state.stage == 3:
    st.subheader("💬 Collaboration")
    
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
                        'content': message,  # <-- FIXED: no extra quotes
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
        if st.button("➡️ View 3D Progress"):
            st.session_state.stage = 4
            st.rerun()

# --- Stage 4: 3D View ---
elif st.session_state.stage == 4:
    st.subheader("🏗️ 3D Design Progress")
    
    # Get design parameters from session state or use defaults
    width = st.session_state.get('width', 5.0)
    depth = st.session_state.get('depth', 3.0)
    length = st.session_state.get('length', 10.0)
    height = st.session_state.get('height', 5.0)
    structure_type = st.session_state.get('structure_type', 'Steel')
    roof_type = st.session_state.get('roof_type', 'Tensile Fabric (PVC/PTFE)')
    
    # View mode selector
    view_modes = ['3D Perspective', 'Plan (Top)', 'Front Elevation', 'Side Elevation']
    selected_view = st.radio("View Mode", view_modes, horizontal=True, key="view_mode")
    
    # Build cache key from inputs
    current_inputs = (width, depth, length, height, structure_type, roof_type, selected_view)
    
    # Check if we need to rebuild the figure
    rebuild_needed = (
        st.session_state.cached_fig is None or
        st.session_state.cached_inputs != current_inputs
    )
    
    if rebuild_needed:
        # Show loading progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔨 Building 3D model... (0%)")
        progress_bar.progress(5)
        time.sleep(0.1)
        
        try:
            # --- Build the 3D model ---
            # 1. Define dimensions
            L = float(length) if length > 0 else 10.0
            W = float(width) if width > 0 else 5.0
            H = float(height) if height > 0 else 5.0
            D = float(depth) if depth > 0 else 3.0
            
            # 2. Define the membrane surface (tensile fabric)
            grid_size = 20
            x = []
            y = []
            z = []
            
            # Generate membrane surface (saddle shape with rise)
            for i in range(grid_size + 1):
                for j in range(grid_size + 1):
                    u = i / grid_size
                    v = j / grid_size
                    x_pos = -L/2 + u * L
                    y_pos = -W/2 + v * W
                    z_pos = H * max(0, (1 - (2*u - 1)**2) * (1 - (2*v - 1)**2))
                    x.append(x_pos)
                    y.append(y_pos)
                    z.append(z_pos)
            
            # Create triangulation for the surface
            triangles = []
            for i in range(grid_size):
                for j in range(grid_size):
                    idx = i * (grid_size + 1) + j
                    idx1 = idx + 1
                    idx2 = idx + (grid_size + 1)
                    idx3 = idx2 + 1
                    triangles.append([idx, idx1, idx2])
                    triangles.append([idx1, idx3, idx2])
            
            triangles_flat = [item for sublist in triangles for item in sublist]
            
            status_text.text("🔨 Building membrane surface... (30%)")
            progress_bar.progress(30)
            time.sleep(0.1)
            
            # --- Create the figure ---
            fig = go.Figure()
            
            # 1. Add membrane surface
            fig.add_trace(go.Mesh3d(
                x=x,
                y=y,
                z=z,
                i=[triangles_flat[i] for i in range(0, len(triangles_flat), 3)],
                j=[triangles_flat[i] for i in range(1, len(triangles_flat), 3)],
                k=[triangles_flat[i] for i in range(2, len(triangles_flat), 3)],
                name='Membrane Surface',
                color='#F5F5F5',
                opacity=0.7,
                flatshading=True,
                showscale=False,
                lighting=dict(ambient=0.5, diffuse=0.8, specular=0.2)
            ))
            
            status_text.text("🔨 Adding structural beams... (60%)")
            progress_bar.progress(60)
            time.sleep(0.1)
            
            # 2. Add primary beams (two along the length)
            beam_positions = [-W/3, W/3]
            beam_color = '#8B8B8B' if structure_type == 'Steel' else '#C0C0C0'
            
            for pos_y in beam_positions:
                fig.add_trace(go.Scatter3d(
                    x=[-L/2, L/2],
                    y=[pos_y, pos_y],
                    z=[0, 0],
                    mode='lines',
                    line=dict(color=beam_color, width=8),
                    name='Primary Beam'
                ))
            
            status_text.text("🔨 Adding structural columns... (80%)")
            progress_bar.progress(80)
            time.sleep(0.1)
            
            # 3. Add columns at corners
            column_positions = [
                (-L/2, -W/3, 0), (-L/2, W/3, 0),
                (L/2, -W/3, 0), (L/2, W/3, 0)
            ]
            for pos_x, pos_y, pos_z in column_positions:
                fig.add_trace(go.Scatter3d(
                    x=[pos_x, pos_x],
                    y=[pos_y, pos_y],
                    z=[0, H/4],
                    mode='lines',
                    line=dict(color='#6B6B6B', width=6),
                    name='Column'
                ))
            
            status_text.text("🔨 Adding dimensions and labels... (95%)")
            progress_bar.progress(95)
            time.sleep(0.1)
            
            # 4. Add dimension lines
            # Length dimension (bottom edge)
            fig.add_trace(go.Scatter3d(
                x=[-L/2, L/2],
                y=[-W/2 - 0.5, -W/2 - 0.5],
                z=[0, 0],
                mode='lines',
                line=dict(color='#FF6B6B', width=2, dash='dash'),
                name='Length'
            ))
            fig.add_trace(go.Scatter3d(
                x=[0],
                y=[-W/2 - 0.5],
                z=[0.1],
                mode='text',
                text=[f"L = {L:.1f} m"],
                textfont=dict(color='#FF6B6B', size=12),
                showlegend=False
            ))
            
            # Width dimension (front edge)
            fig.add_trace(go.Scatter3d(
                x=[-L/2 - 0.5, -L/2 - 0.5],
                y=[-W/3, W/3],
                z=[0, 0],
                mode='lines',
                line=dict(color='#4ECDC4', width=2, dash='dash'),
                name='Width'
            ))
            fig.add_trace(go.Scatter3d(
                x=[-L/2 - 0.5],
                y=[0],
                z=[0.1],
                mode='text',
                text=[f"W = {W:.1f} m"],
                textfont=dict(color='#4ECDC4', size=12),
                showlegend=False
            ))
            
            # Height dimension (at center)
            fig.add_trace(go.Scatter3d(
                x=[L/2 + 0.5, L/2 + 0.5],
                y=[0, 0],
                z=[0, H],
                mode='lines',
                line=dict(color='#FFD93D', width=2, dash='dash'),
                name='Height'
            ))
            fig.add_trace(go.Scatter3d(
                x=[L/2 + 0.5],
                y=[0],
                z=[H/2],
                mode='text',
                text=[f"H = {H:.1f} m"],
                textfont=dict(color='#FFD93D', size=12),
                showlegend=False
            ))
            
            status_text.text("🔨 Setting up view... (100%)")
            progress_bar.progress(100)
            time.sleep(0.1)
            
            # 5. Configure scene based on selected view
            scene_config = dict(
                bgcolor='#1E1E1E',
                xaxis=dict(title='Length (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
                yaxis=dict(title='Width (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
                zaxis=dict(title='Height (m)', color='#B0B0B0', gridcolor='#2A2A2A'),
                aspectmode='manual',
                aspectratio=dict(x=L/5, y=W/5, z=H/5) if L > 0 and W > 0 and H > 0 else dict(x=1, y=1, z=1)
            )
            
            # Set camera based on view mode
            camera_dict = dict(
                eye=dict(x=2.0, y=2.0, z=1.5)
            )
            if selected_view == 'Plan (Top)':
                camera_dict = dict(eye=dict(x=0, y=0, z=3))
            elif selected_view == 'Front Elevation':
                camera_dict = dict(eye=dict(x=0, y=3, z=0))
            elif selected_view == 'Side Elevation':
                camera_dict = dict(eye=dict(x=3, y=0, z=0))
            
            fig.update_layout(
                scene=scene_config,
                scene_camera=camera_dict,
                paper_bgcolor='#1E1E1E',
                plot_bgcolor='#1E1E1E',
                margin=dict(l=0, r=0, t=0, b=0),
                height=500,
                showlegend=False,
                font=dict(color='#B0B0B0')
            )
            
            # Cache the figure
            st.session_state.cached_fig = fig
            st.session_state.cached_inputs = current_inputs
            
            status_text.text("✅ Model ready!")
            time.sleep(0.2)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error building 3D model: {str(e)}")
            # Create fallback simple figure
            fig = go.Figure()
            fig.add_trace(go.Scatter3d(
                x=[0, 1, 1, 0, 0, 1, 1, 0],
                y=[0, 0, 1, 1, 0, 0, 1, 1],
                z=[0, 0, 0, 0, 1, 1, 1, 1],
                mode='markers',
                marker=dict(size=5, color='#00B4D8')
            ))
            fig.update_layout(
                scene=dict(bgcolor='#1E1E1E'),
                paper_bgcolor='#1E1E1E',
                margin=dict(l=0, r=0, t=0, b=0),
                height=400
            )
            st.session_state.cached_fig = fig
            st.session_state.cached_inputs = current_inputs
    else:
        # Use cached figure
        fig = st.session_state.cached_fig
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True, key="3d_viewer")
    
    # --- Design Summary ---
    st.subheader("📋 Design Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Length (L)", f"{length:.1f} m")
    with col2:
        st.metric("Width (W)", f"{width:.1f} m")
    with col3:
        st.metric("Height (H)", f"{height:.1f} m")
    with col4:
        st.metric("Depth (D)", f"{depth:.1f} m")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Structure Type", structure_type)
    with col2:
        st.metric("Roof Type", roof_type)
    with col3:
        st.metric("Status", "Draft")
    
    # --- Navigation ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Collaboration"):
            st.session_state.stage = 3
            st.rerun()
    with col2:
        if st.button("📌 Freeze Concept"):
            st.session_state.stage = 5
            st.rerun()

# --- Stage 5: Concept Freeze ---
elif st.session_state.stage == 5:
    st.subheader("📌 Freeze Concept")
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
