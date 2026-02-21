import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
import json

st.set_page_config(page_title="AP Agent Dashboard", page_icon="🏦", layout="wide")
st.title("🏦 Sahir's Enterprise AP Auditor")

# 1. INITIALIZE SESSION STATE
if 'history' not in st.session_state:
    st.session_state.history = []

# 2. SECURE KEY LOADING
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

# 3. SIDEBAR CONTROLS
with st.sidebar:
    st.header("Audit Settings")
    tolerance = st.slider("Variance Tolerance (%)", 0.0, 5.0, 1.0)
    st.info(f"Policy: Flag if variance > {tolerance}%")
    st.divider()
    st.write("Target: Fall 2026 Audit Ready")

# 4. MAIN INTERFACE
col1, col2 = st.columns(2)
with col1:
    po_file = st.file_uploader("1. Purchase Order (PDF)", type="pdf")
with col2:
    inv_file = st.file_uploader("2. Invoice (PDF)", type="pdf")

if po_file and inv_file:
    if st.button("🚀 Run Enterprise Audit"):
        with st.spinner('Performing Forensic Comparison...'):
            
            # 1. CLEAN TEXT EXTRACTION
            def get_clean_text(file):
                text = "".join([p.extract_text() for p in PdfReader(file).pages])
                clean_text = text.replace('{', '[').replace('}', ']').strip()
                return clean_text

            po_text = get_clean_text(po_file)
            inv_text = get_clean_text(inv_file)
            
            # 2. BULLETPROOF PROMPT (Multi-Currency & Risk)
            prompt = f"""
            You are a Senior Forensic Accountant. Compare the PO and Invoice.
            
            TASKS:
            1. Detect CURRENCY for both (e.g., USD, CAD). If different, convert Invoice to PO currency.
            2. Compare Totals. Calculate variance %.
            3. Assign RISK LEVEL: 
               - 'LOW (Green)' if variance < {tolerance}%
               - 'MEDIUM (Yellow)' if variance between {tolerance}% and 5%
               - 'HIGH (Red)' if variance > 5% or unauthorized items found.
            
            PURCHASE ORDER DATA:
            {po_text}
            
            INVOICE DATA:
            {inv_text}
            
            Output ONLY a JSON object with these keys: 
            vendor, inv
