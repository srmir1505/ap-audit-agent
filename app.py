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
            po_text = "".join([p.extract_text() for p in PdfReader(po_file).pages])
            inv_text = "".join([p.extract_text() for p in PdfReader(inv_file).pages])
            
            # UPGRADED SYSTEM PROMPT: Now handles Multi-Currency & Risk Scoring
            prompt = f"""
            You are a Senior Forensic Accountant. Compare the PO and Invoice.
            
            TASKS:
           if po_file and inv_file:
    if st.button("🚀 Run Enterprise Audit"):
        with st.spinner('Performing Forensic Comparison...'):
            # 1. CLEAN TEXT EXTRACTION
            def get_clean_text(file):
                text = "".join([p.extract_text() for p in PdfReader(file).pages])
                return text.replace('{', '[').replace('}', ']').strip() # Remove JSON-breaking chars

            po_text = get_clean_text(po_file)
            inv_text = get_clean_text(inv_file)
            
            # 2. BULLETPROOF PROMPT
            # We explicitly tell it to return ONLY JSON and nothing else
            prompt = f"""
            System: Senior Forensic Accountant
            Goal: Compare PO and Invoice.
            
            Rule: Flag 'human_review': true if variance > {tolerance}%.
            
            PURCHASE ORDER DATA:
            {po_text}
            
            INVOICE DATA:
            {inv_text}
            
            Output ONLY a JSON object with these keys: 
            vendor, inv_amt, inv_currency, po_amt, po_currency, variance_pct, risk_level, human_review, review_reason.
            """
            
            # 3. CALL MODEL
            try:
                response = model.generate_content(prompt)
                
                # Check if the response actually has text
                if not response.text:
                    st.error("AI returned an empty response. Try simplifying the PDF.")
                    st.stop()
                    "Vendor": res.get("vendor"),
                    "Invoice": f"{res.get('inv_amt')} {res.get('inv_currency')}",
                    "PO": f"{res.get('po_amt')} {res.get('po_currency')}",
                    "Variance": f"{res.get('variance_pct')}%",
                    "Risk": res.get("risk_level"),
                    "Status": "🚨 REVIEW" if res.get("human_review") else "✅ CLEAR"
                })
                
                st.success("Audit Complete!")
                st.json(res)
            except Exception as e:
                st.error(f"Audit Error: {e}")

# 5. THE AUDIT LOG & EXPORT
if st.session_state.history:
    st.divider()
    st.subheader("📊 Multi-Doc Audit Log")
    df = pd.DataFrame(st.session_state.history)
    
    # Apply Visual Color Scoring to the table
    def color_risk(val):
        color = 'red' if 'HIGH' in val else 'orange' if 'MEDIUM' in val else 'green'
        return f'color: {color}; font-weight: bold'
    
    st.table(df.style.applymap(color_risk, subset=['Risk']))
    
    # 6. EXPORT BUTTON
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Audit Trail (CSV)",
        data=csv,
        file_name="ap_audit_trail_export.csv",
        mime="text/csv",
    )

