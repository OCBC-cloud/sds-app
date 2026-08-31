import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import uuid
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="SDS Stakeholder Input Portal",
    page_icon="🏗️",
    layout="wide"
)

# --- Supabase Credentials ---
SUPABASE_URL = "https://pcijgufnjeijqqywubpu.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- App Title ---
st.title("🏗️ SDS Stakeholder Input Portal")
st.caption("Tensile Membrane Structure Design | Upload Sketches, Photos, GPS Images")

# --- Sidebar ---
with st.sidebar:
    st.header("📊 Project Info")
    
    # Project selector
    project_name = st.text_input("Project Name", placeholder="e.g., Taman Megah Canopy")
    client_name = st.text_input("Client Name (optional)", placeholder="e.g., Tuan Haji Ahmad")
    
    st.divider()
    st.caption("📱 Upload sketches, photos, and GPS-tagged images")
    st.caption("🧬 Knowledge may evolve. 🌱 Identity shall remain.")

# --- Main Upload Form ---
st.subheader("📤 Upload Design Inputs")

col1, col2 = st.columns(2)

with col1:
    design_phase = st.selectbox(
        "Design Phase",
        ["Concept", "Schematic", "Detailed", "Construction"]
    )
    
    material_family = st.selectbox(
        "Material Family",
        ["Steel", "Aluminium", "Timber", "Tensile Fabric (PVC/PTFE)", "ETFE/PTFE Cushion"]
    )
    
    # Dynamic standard mapping based on material
    standard_mapping = {
        "Steel": ["MS (EN)", "AISC", "GB", "AS/NZS"],
        "Aluminium": ["MS (EN)", "AISC", "GB", "AS/NZS"],
        "Timber": ["MS (EN)", "NDS", "GB", "AS/NZS"],
        "Tensile Fabric (PVC/PTFE)": ["MS (EN)", "ASCE 55", "TensiNet"],
        "ETFE/PTFE Cushion": ["MS (EN)", "ASCE 55", "TensiNet"]
    }
    
    design_standard = st.selectbox(
        "Design Standard",
        standard_mapping.get(material_family, ["MS (EN)"])
    )

with col2:
    st.markdown("### 📍 Location")
    
    gps_lat = st.number_input("Latitude", value=3.1390, format="%.6f", help="e.g., 3.1390")
    gps_lng = st.number_input("Longitude", value=101.6869, format="%.6f", help="e.g., 101.6869")
    
    st.caption("📍 Default: Kuala Lumpur (3.1390° N, 101.6869° E)")

# --- Image Upload ---
st.subheader("🖼️ Upload Images")

uploaded_files = st.file_uploader(
    "Choose images (JPG/PNG, max 10MB each)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    help="Upload sketches, photos of existing structures, or site inspiration"
)

# --- Additional Notes ---
notes = st.text_area("Additional Notes", placeholder="Any observations, constraints, or client feedback...", max_chars=500)

# --- Submit Button ---
submitted = st.button("📤 Submit to Project", type="primary")

# --- Process Submission ---
if submitted:
    if not project_name:
        st.error("❌ Project Name is required.")
    elif not uploaded_files:
        st.error("❌ At least one image must be uploaded.")
    else:
        with st.spinner("Uploading to Supabase..."):
            try:
                # 1. Create project
                project_data = {
                    'name': project_name,
                    'client_name': client_name if client_name else None,
                    'created_by': str(uuid.uuid4())  # placeholder - will link to auth later
                }
                project_result = supabase.table('projects').insert(project_data).execute()
                project_id = project_result.data[0]['id']
                
                # 2. Create design iteration
                iteration_data = {
                    'project_id': project_id,
                    'version_number': 1,
                    'material': material_family,
                    'standard': design_standard,
                    'notes': notes if notes else None,
                    'gps_lat': gps_lat,
                    'gps_lng': gps_lng,
                    'uploaded_by': str(uuid.uuid4())  # placeholder
                }
                iteration_result = supabase.table('design_iterations').insert(iteration_data).execute()
                iteration_id = iteration_result.data[0]['id']
                
                # 3. Upload each image
                uploaded_count = 0
                for img in uploaded_files:
                    # Read image
                    image_data = img.read()
                    
                    # Try to extract GPS from EXIF
                    exif_gps_lat = None
                    exif_gps_lng = None
                    try:
                        pil_img = Image.open(io.BytesIO(image_data))
                        exif = pil_img._getexif()
                        if exif:
                            for tag_id, value in exif.items():
                                tag = TAGS.get(tag_id, tag_id)
                                if tag == "GPSInfo":
                                    gps_info = {}
                                    for gps_tag in value:
                                        sub_tag = GPSTAGS.get(gps_tag, gps_tag)
                                        gps_info[sub_tag] = value[gps_tag]
                                    
                                    # Convert GPS to decimal
                                    def convert_to_degrees(value):
                                        d = float(value[0])
                                        m = float(value[1])
                                        s = float(value[2])
                                        return d + (m / 60.0) + (s / 3600.0)
                                    
                                    if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                                        lat = convert_to_degrees(gps_info['GPSLatitude'])
                                        lng = convert_to_degrees(gps_info['GPSLongitude'])
                                        if gps_info.get('GPSLatitudeRef') == 'S':
                                            lat = -lat
                                        if gps_info.get('GPSLongitudeRef') == 'W':
                                            lng = -lng
                                        exif_gps_lat = lat
                                        exif_gps_lng = lng
                    except Exception as e:
                        # EXIF extraction failed - use user-provided or default
                        pass
                    
                    # Use user-provided GPS if EXIF not found
                    if exif_gps_lat is None:
                        exif_gps_lat = gps_lat
                        exif_gps_lng = gps_lng
                    
                    # Upload to Supabase Storage
                    file_path = f"projects/{project_id}/{iteration_id}/{img.name}"
                    supabase.storage.from_('design-uploads').upload(file_path, image_data)
                    
                    # Store image metadata
                    image_record = {
                        'iteration_id': iteration_id,
                        'storage_path': file_path,
                        'filename': img.name,
                        'mime_type': img.type,
                        'exif_gps_lat': exif_gps_lat,
                        'exif_gps_lng': exif_gps_lng
                    }
                    supabase.table('images').insert(image_record).execute()
                    uploaded_count += 1
                
                st.success(f"✅ Successfully uploaded {uploaded_count} images to project: {project_name}")
                st.info(f"📍 Location: {gps_lat:.6f}, {gps_lng:.6f}")
                st.info(f"📐 Material: {material_family} | Standard: {design_standard}")
                
            except Exception as e:
                st.error(f"❌ Upload error: {str(e)}")

# --- Footer ---
st.divider()
st.caption("🧬 Knowledge may evolve. 🌱 Identity shall remain.")
st.caption("SDS Chamber 002 – Stakeholder Input Portal (Phase 1.1 POC)")
