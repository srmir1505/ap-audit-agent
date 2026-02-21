import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
import json


if 'history' not in st.session_state:
    st.session_state.history = []


st.set_page_config(page_title="AP Agent Dashboard", page_icon="🏦", layout="wide")
st.title("🏦 Sahir's AP Specialist AI")

if 'history' not in st.session_state:
    st.session_state.history = []

genai.configure(api_key="AIzaSyAm90SoKYJXY9-0CehsHLmIcUcVhcn7W2Q") # Replace with your ...7W2Q key
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- SIDEBAR FOR SETTINGS ---
with st.sidebar:
    st.header("Audit Settings")
    tolerance = st.slider("Variance Tolerance (%)", 0.0, 5.0, 1.0)
    st.info(f"Current Policy: Flag if > {tolerance}%")

# --- MAIN DASHBOARD ---
col1, col2 = st.columns(2)
with col1:
    po_file = st.file_uploader("1. Upload Purchase Order (PDF)", type="pdf")
with col2:
    inv_file = st.file_uploader("2. Upload Invoice (PDF)", type="pdf")

if po_file and inv_file:
    if st.button("🚀 Run Full Audit"):
        with st.spinner('Comparing documents...'):
            # Extract text from both
            po_text = "".join([p.extract_text() for p in PdfReader(po_file).pages])
            inv_text = "".join([p.extract_text() for p in PdfReader(inv_file).pages])
            
            prompt = f"""
            You are a Senior AP Auditor. Compare the PURCHASE ORDER text and the INVOICE text.
            1. Extract Vendor Name and Total Amount from the Invoice.
            2. Compare Invoice Total vs PO Total.
            3. Set 'human_review' to true if variance is > {tolerance}%.
            
            PO TEXT: {po_text}
            INVOICE TEXT: {inv_text}
            
            Return ONLY JSON with: vendor_name, total_amount, po_total, variance_pct, human_review, review_reason.
            """
            
            response = model.generate_content(prompt)
            
            try:
                raw_text = response.text.replace('```json', '').replace('```', '').strip()
                res_json = json.loads(raw_text)
                
                # Update History
                st.session_state.history.append({
                    "Vendor": res_json.get("vendor_name"),
                    "Invoice Amt": f"${res_json.get('total_amount'):,.2f}",
                    "PO Amt": f"${res_json.get('po_total'):,.2f}",
                    "Variance": f"{res_json.get('variance_pct')}%",
                    "Status": "🚨 REVIEW" if res_json.get("human_review") else "✅ MATCHED"
                })
                
                st.success("Audit Complete!")
                st.json(res_json)
            except Exception as e:
                st.error(f"Audit Failed: {e}")

# --- AUDIT LOG ---
if st.session_state.history:
    st.divider()
    st.subheader("📊 Multi-Doc Audit Log")
    st.table(pd.DataFrame(st.session_state.history))
