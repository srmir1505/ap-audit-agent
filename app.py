import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
import json

# Set wide layout and custom title
st.set_page_config(page_title="AP Agent Dashboard", page_icon="", layout="wide")

# --- 🎨 SAFE LIGHTWEIGHT CSS ---
st.markdown("""
    <style>
    /* Hide default Streamlit footer */
    footer {visibility: hidden;}
    
    /* Apply Apple system fonts */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Clean, slightly rounded buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 MODERN SECURE LOGIN GATEWAY ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.write("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🔒 Secure System Access</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sahir's Enterprise AP Auditor</p>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.text_input("Password", type="password", on_change=password_entered, key="password", placeholder="Enter your password...")
        return False
    elif not st.session_state["password_correct"]:
        st.write("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🔒 Secure System Access</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sahir's Enterprise AP Auditor</p>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.text_input("Password", type="password", on_change=password_entered, key="password", placeholder="Enter your password...")
            st.error("Authentication Failed. Please try again.")
        return False
    return True

# --- 🚀 MAIN APPLICATION ---
if check_password():
    
    # 1. INITIALIZE SESSION STATE
    if 'history' not in st.session_state:
        st.session_state.history = []

    # 2. SECURE KEY LOADING
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3-flash-preview')

    # --- HEADER & KPI DASHBOARD ---
    st.markdown("<h1>Enterprise AP Auditor</h1>", unsafe_allow_html=True)
    st.caption("Automated 3-Way Matching, Cross-Border Conversion & Forensic Risk Scoring")
    st.write("") 

    total_audits = len(st.session_state.history)
    high_risk_count = sum(1 for item in st.session_state.history if "HIGH" in str(item.get("Risk", "")).upper())

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Documents Audited", total_audits)
    col_m2.metric("High-Risk Flags", high_risk_count, delta_color="inverse")
    col_m3.metric("System Status", "Securely Connected" if api_key else "Offline")
    st.divider()

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.header("⚙️ Preferences")
        tolerance = st.slider("Variance Tolerance (%)", 0.0, 5.0, 1.0)
        st.info(f"Active Policy: Flag if > {tolerance}%")
        st.divider()
        st.write("Target: Fall 2026 Audit Ready")
        st.write("")
        if st.button("Log Out / End Session"):
            st.session_state["password_correct"] = False
            st.rerun()

    # --- MAIN UPLOAD INTERFACE ---
    col1, col2 = st.columns(2)
    with col1:
        po_file = st.file_uploader("1. Upload Purchase Order (PDF)", type="pdf")
    with col2:
        inv_file = st.file_uploader("2. Upload Invoice (PDF)", type="pdf")

    # --- EXECUTION LOGIC ---
    if po_file and inv_file:
        st.write("")
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            run_audit = st.button("🚀 Run Forensic Audit", use_container_width=True)

        if run_audit:
            with st.spinner('Analyzing documents & calculating currency variances...'):
                
                def get_clean_text(file):
                    text = "".join([p.extract_text() for p in PdfReader(file).pages])
                    return text.replace('{', '[').replace('}', ']').strip()

                po_text = get_clean_text(po_file)
                inv_text = get_clean_text(inv_file)
                
                prompt = f"""
                You are a Senior Forensic Accountant. Compare the PO and Invoice.
                
                TASKS:
                1. Detect CURRENCY for both. If different, convert Invoice to PO currency.
                2. Compare Totals. Calculate variance %.
                3. Detect UNAUTHORIZED ITEMS (any line items on the invoice not present on the PO).
                4. Assign RISK LEVEL: 
                   - 'LOW (Green)' if variance <= {tolerance}% AND no unauthorized items.
                   - 'MEDIUM (Yellow)' if variance > {tolerance}% but <= 5% AND no unauthorized items.
                   - 'HIGH (Red)' if variance > 5% OR unauthorized items are found.
                5. Assign ISSUE TYPE: Give a concise 1-3 word root cause category.
                
                PURCHASE ORDER DATA:
                {po_text}
                
                INVOICE DATA:
                {inv_text}
                
                Output ONLY a valid JSON object with EXACTLY these keys: 
                vendor, inv_amt, inv_currency, po_amt, po_currency, variance_pct, risk_level, issue_type, human_review, review_reason.
                """
                
                try:
                    response = model.generate_content(prompt)
                    
                    if not response.text:
                        st.error("AI returned an empty response. Try simplifying the PDF.")
                        st.stop()
                    
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    res = json.loads(raw_json)
                    
                    st.session_state.history.append({
                        "Vendor": res.get("vendor"),
                        "Invoice": f"{res.get('inv_amt')} {res.get('inv_currency')}",
                        "PO": f"{res.get('po_amt')} {res.get('po_currency')}",
                        "Variance": f"{res.get('variance_pct')}%",
                        "Issue Type": res.get("issue_type", "Unknown"),
                        "Risk": res.get("risk_level"),
                        "Status": "🚨 REVIEW" if res.get("human_review") else "✅ CLEAR"
                    })
                    
                    st.success(f"Audit Complete! Flagged Reason: {res.get('review_reason')}")
                    
                    with st.expander("🔍 View Raw System Log (JSON)"):
                        st.json(res)
                        
                except Exception as e:
                    st.error(f"Audit Error: {e}")

    # --- THE AUDIT LOG & EXPORT ---
    if st.session_state.history:
        st.write("")
        st.subheader("📊 Enterprise Audit Trail")
        df = pd.DataFrame(st.session_state.history)
        
        cols = ["Vendor", "Invoice", "PO", "Variance", "Issue Type", "Risk", "Status"]
        df = df[[c for c in cols if c in df.columns]]
        
        if 'Risk' in df.columns:
            def color_risk(val):
                val_str = str(val).upper()
                color = 'red' if 'HIGH' in val_str else 'orange' if 'MEDIUM' in val_str else 'green'
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(df.style.map(color_risk, subset=['Risk']), use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        _, dl_col, _ = st.columns([1, 2, 1])
        with dl_col:
            st.download_button(
                label="📥 Export Secure Audit Log (CSV)",
                data=csv,
                file_name="ap_audit_trail_export.csv",
                mime="text/csv",
                use_container_width=True
            )
