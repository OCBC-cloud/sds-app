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
    /* Main background */
    .stApp {
        background-color: #1E1E1E;
    }
    /* Sidebar */
    .css-1d391kg {
        background-color: #2A2A2A;
    }
    /* Input fields */
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #2D2D2D !important;
        color: #E0E0E0 !important;
        border: 1px solid #3A3A3A !important;
        border-radius: 8px !important;
    }
    /* Dropdowns */
    .stSelectbox select {
        background-color: #3A3A3A !important;
        color: #E0E0E0 !important;
        border: 1px solid #4A4A4A !important;
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
        color: #F0F0F0 !important;
    }
    /* Captions */
    .stCaption, .stMarkdown p {
        color: #B0B0B0 !important;
    }
    /* Success messages */
    .stAlert {
        background-color: #2A3A2A !important;
        border-color: #52B788 !important;
        color: #D4EDDA !important;
    }
    /* Error messages */
    .stError {
        background-color: #3A2A2A !important;
        border-color: #E63946 !important;
        color: #F8D7DA !important;
    }
    /* Info messages */
    .stInfo {
        background-color: #2A3A4A !important;
        border-color: #00B4D8 !important;
        color: #D4EDF4 !important;
    }
    /* Divider */
    hr {
        border-color: #3A3A3A !important;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #2A2A2A;
        color: #B0B0B0;
        border-radius: 8px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3A3A3A;
        color: #F0F0F0 !important;
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

# --- App Title ---
st.title("🏗️ SDS Design Portal")
st.caption("Tensile Membrane Structure Design | Multi-Stage Input Portal")

# --- Stage Navigation ---
stages = ["1. Project Registration", "2. Design Input", "3. Collaboration", "4. 3D View", "5. Concept Freeze"]
current_stage = st.session_state.stage - 1
st.progress((current_stage + 1) / len(stages))
st.caption(f"Stage {st.session_state.stage} of {len(stages)}: {stages[current_stage]}")

# --- Reset Function ---
def reset_field(field_name):
    if field_name in st.session_state:
        del st.session_state[field_name]
    st.rerun()

# --- Stage 1: Project Registration ---
if st.session_state.stage == 1:
    st.subheader("📋 Project Registration")
    
    with st.form("project_registration"):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("Project Name *", placeholder="e.g., Taman Megah Canopy", key="proj_name")
            st.caption("↺ Reset", unsafe_allow_html=True)
            if st.button("Reset Project Name", key="reset_proj_name"):
                reset_field("proj_name")
            
            client_name = st.text_input("Client Name", placeholder="e.g., Tuan Haji Ahmad", key="client_name")
            if st.button("Reset Client Name", key="reset_client"):
                reset_field("client_name")
            
            main_contractor = st.text_input("Main Contractor", placeholder="e.g., Bina Sdn Bhd", key="main_contractor")
            if st.button("Reset Main Contractor", key="reset_contractor"):
                reset_field("main_contractor")
        
        with col2:
            contact_phone = st.text_input("Contact Phone", placeholder="e.g., 012-3456789", key="contact_phone")
            if st.button("Reset Contact Phone", key="reset_phone"):
                reset_field("contact_phone")
            
            contact_email = st.text_input("Contact Email", placeholder="e.g., client@email.com", key="contact_email")
            if st.button("Reset Contact Email", key="reset_email"):
                reset_field("contact_email")
            
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
    
    with st.form("design_input"):
        col1, col2 = st.columns(2)
        
        with col1:
            description = st.text_area("General Description", placeholder="Describe the design concept, site context, and key requirements...", key="description")
            if st.button("Reset Description", key="reset_desc"):
                reset_field("description")
            
            width = st.number_input("Width (m)", value=0.0, step=0.1, key="width")
            if st.button("Reset Width", key="reset_width"):
                reset_field("width")
            
            depth = st.number_input("Depth (m)", value=0.0, step=0.1, key="depth")
            if st.button("Reset Depth", key="reset_depth"):
                reset_field("depth")
        
        with col2:
            length = st.number_input("Length (m)", value=0.0, step=0.1, key="length")
            if st.button("Reset Length", key="reset_length"):
                reset_field("length")
            
            height = st.number_input("Height (m)", value=0.0, step=0.1, key="height")
            if st.button("Reset Height", key="reset_height"):
                reset_field("height")
            
            structure_type = st.selectbox("Structure Type", ["Steel", "Aluminium", "Timber", "Other"], key="structure_type")
            if st.button("Reset Structure Type", key="reset_structure"):
                reset_field("structure_type")
            
            roof_type = st.selectbox("Roof Type", ["Tensile Fabric (PVC/PTFE)", "ETFE Cushion", "Other"], key="roof_type")
            if st.button("Reset Roof Type", key="reset_roof"):
                reset_field("roof_type")
        
        # Image Upload
        st.subheader("🖼️ Upload Images")
        uploaded_files = st.file_uploader(
            "Choose images (JPG/PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="design_images",
            help="Upload sketches, photos of existing structures, or site inspiration"
        )
        if st.button("Clear Images", key="clear_images"):
            reset_field("design_images")
        
        # Sketch Board (placeholder)
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
                    
                    # Upload images
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
    
    with st.form("collaboration"):
        stakeholder = st.selectbox("Communicate with", ["Owner", "Architect", "Engineer", "Other"], key="stakeholder")
        if st.button("Reset Stakeholder", key="reset_stakeholder"):
            reset_field("stakeholder")
        
        message = st.text_area("Your Message", placeholder="Share feedback, questions, or design ideas...", key="message")
        if st.button("Reset Message", key="reset_message"):
            reset_field("message")
        
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
        if st.button("➡️ View 3D Progress"):
            st.session_state.stage = 4
            st.rerun()

# --- Stage 4: 3D View ---
elif st.session_state.stage == 4:
    st.subheader("🏗️ 3D Design Progress")
    
    st.info("📐 Simple 3D visualization of your design")
    
    # Simple 3D box using plotly
    fig = go.Figure(data=[
        go.Mesh3d(
            x=[0, 1, 1, 0, 0, 1, 1, 0],
            y=[0, 0, 1, 1, 0, 0, 1, 1],
            z=[0, 0, 0, 0, 1, 1, 1, 1],
            color='#00B4D8',
            opacity=0.5
        )
    ])
    fig.update_layout(
        scene=dict(
            xaxis_title="Width",
            yaxis_title="Depth",
            zaxis_title="Height",
            bgcolor="#1E1E1E",
            xaxis=dict(color="#E0E0E0"),
            yaxis=dict(color="#E0E0E0"),
            zaxis=dict(color="#E0E0E0")
        ),
        paper_bgcolor="#1E1E1E",
        plot_bgcolor="#1E1E1E",
        margin=dict(l=0, r=0, t=0, b=0),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("🔲 Simple 3D representation of your design dimensions")
    
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
