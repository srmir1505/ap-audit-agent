import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
import json

# Set wide layout and custom title
st.set_page_config(page_title="AP Agent Dashboard", page_icon="🏦", layout="wide")

# --- 🎨 CUSTOM APPLE-STYLE CSS INJECTION ---
st.markdown("""
    <style>
    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Apply Apple system fonts */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Sleek, rounded buttons like iOS/macOS */
    .stButton > button {
        border-radius: 20px;
        border: 1px solid #d2d2d7;
        background-color: #ffffff;
        color: #1d1d1f;
        font-weight: 600;
        transition: all 0.3s ease;
        padding: 10px 24px;
    }
    .stButton > button:hover {
        border-color: #0071e3;
        color: #0071e3;
        box-shadow: 0 4px 14px rgba(0,113,227,0.15);
        transform: translateY(-1px);
    }
    
    /* Minimalist Metric Cards with soft shadows */
    div[data-testid="metric-container"] {
        background-color: #fbfbfd;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #e5e5ea;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    
    /* Clean File Uploader Box */
    div[data-testid="stFileUploader"] {
        border: 1.5px dashed #d2d2d7;
        border-radius: 20px;
        background-color: #fbfbfd;
        padding: 15px;
        transition: all 0.3s ease;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #0071e3;
        background-color: #f5f5f7;
    }
    
    /* Clean up the dataframe visual */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #e5e5ea;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 SECURE LOGIN GATEWAY ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align: center; color: #1d1d1f;'>🔒 Forensic Access</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #86868b;'>Please authenticate to continue.</p>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.text_input("Secure Password", type="password", on_change=password_entered, key="password", label_visibility="collapsed", placeholder="Enter Password...")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h1 style='text-align: center; color: #1d1d1f;'>🔒 Forensic Access</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #86868b;'>Please authenticate to continue.</p>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.text_input("Secure Password", type="password", on_change=password_entered, key="password", label_visibility="collapsed", placeholder="Enter Password...")
            st.error("Authentication Failed.")
        return False
    return True

# --- 🚀 MAIN APPLICATION ---
if check_password():
    
    if 'history' not in st.session_state:
        st.session_state.history = []

    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3-flash-preview')

    # --- HEADER & KPI DASHBOARD ---
    st.markdown("<h1 style='color: #1d1d1f;'>Enterprise AP Auditor</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #86868b; font-size: 1.1rem;'>Automated 3-Way Matching & Forensic Risk Scoring</p>", unsafe_allow_html=True)
    st.write("") # Whitespace

    total_audits = len(st.session_state.history)
    high_risk_count = sum(1 for item in st.session_state.history if "HIGH" in str(item.get("Risk", "")).upper())

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Documents Audited", total_audits)
    col_m2.metric("High-Risk Flags", high_risk_count, delta_color="inverse")
    col_m3.metric("System Status", "Securely Connected" if api_key else "Offline")
    st.write("") # Whitespace
