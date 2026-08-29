import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="SDS Steward Console", page_icon="🌱", layout="wide")

SUPABASE_URL = "https://pcijgufnjeijqqywubpu.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🌱 SDS Chamber 002 – Steward Console")
st.caption("Nutrient Cycle Management | KPI Ingestion & Adaptation Binding")

with st.sidebar:
    st.header("📊 System Status")
    st.success("✅ Connected to Supabase")
    st.info("Phase 1: Manual Mode")
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))

tab1, tab2, tab3 = st.tabs(["📤 Upload KPI Data", "🔗 Bind Adaptation", "📋 View Bindings"])

with tab1:
    st.header("📤 Upload KPI Data")
    uploaded_file = st.file_uploader("Choose CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.dataframe(df.head())
        if st.button("Upload"):
            st.success("Upload feature ready")

with tab2:
    st.header("🔗 Bind Adaptation")
    st.info("Bind an adaptation to a KPI")

with tab3:
    st.header("📋 View Bindings")
    st.info("View all active bindings")

st.divider()
st.caption("🧬 Knowledge may evolve. 🌱 Identity shall remain.")
