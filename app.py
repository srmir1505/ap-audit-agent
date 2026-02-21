import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
import json

# 1. PAGE CONFIG
st.set_page_config(page_title="AP Agent Pro", page_icon="🔍", layout="wide")

# 2. SESSION STATE
if 'history' not in st.session_state:
    st.session_state.history = []

# 3. SECURE KEY LOADING
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- 🛠️ HELPER FUNCTIONS ---
def get_clean_text(file):
    text = "".join([p.extract_text() for p in PdfReader(file).pages])
    return text.replace('{', '[').replace('}', ']').strip()

@st.dialog("Forensic Breakdown")
def show_details(res):
    st.write(f"**Reasoning:** {res.get('review_reason')}")
    st.divider()
    st.json(res)
    if st.button("Close"):
        st.rerun()

# --- 📱 MAIN UI ---
st.title("🕵️ Forensic AP Auditor")
st.caption("Advanced AI Analysis for High-Volume Accounts Payable")

# --- SIDEBAR: PRECISION CONTROLS ---
with st.sidebar:
    st.header("📊 Session Intelligence")
    if st.session_state.history:
        df_stats = pd.DataFrame(st.session_state.history)
        st.metric("Total Audits", len(df_stats))
        high_risk = len(df_stats[df_stats['Risk'].str.contains("HIGH")])
        st.metric("High Risk Flags", high_risk, delta=high_risk, delta_color="inverse")
    
    st.divider()
    
    # NEW: DUAL-INPUT SYSTEM FOR PRECISION
    st.header("⚙️ Audit Policy")
    input_val = st.number_input("Type exact % tolerance:", min_value=0.0, max_value=10.0, value=1.0, step=0.01)
    tolerance = st.slider("Or use slider:", 0.0, 10.0, value=input_val, step=0.1)
    
    # Syncing: This ensures the policy always uses the numeric input if it changes
    final_policy = input_val if input_val != 1.0 else tolerance
    
    st.info(f"Active Policy: Flag if > {final_policy}%")
    st.divider()
    if st.button("Clear Session"):
        st.session_state.history = []
        st.rerun()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📥 Ingestion", "📋 Audit Trail", "📈 Insights"])

with tab1:
    st.markdown("### Step 1: Document Upload")
    c1, c2 = st.columns(2)
    with c1:
        po_file = st.file_uploader("Authorized Purchase Order", type="pdf")
    with c2:
        inv_file = st.file_uploader("Incoming Vendor Invoice", type="pdf")
    
    if po_file and inv_file:
        st.success("Documents Loaded.")
        if st.button("🚀 Execute Forensic Audit", use_container_width=True):
            with st.spinner('Scanning for discrepancies...'):
                po_text = get_clean_text(po_file)
                inv_text = get_clean_text(inv_file)
                
                prompt = f"""
                Analyze these documents as a Forensic Accountant.
                1. Detect Currency & Convert to PO Currency.
                2. Check Variance. Tolerance is {final_policy}%.
                3. Risk: LOW if variance < {final_policy}% & no extra items. 
                   MEDIUM if variance between {final_policy}% and 5%. 
                   HIGH if extra items or variance > 5%.
                
                PO: {po_text}
                INV: {inv_text}
                
                Output ONLY JSON: {{vendor, inv_amt, inv_currency, po_amt, po_currency, variance_pct, risk_level, issue_type, human_review, review_reason}}
                """
                
                response = model.generate_content(prompt)
                res = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                
                st.session_state.history.append({
                    "Vendor": res.get("vendor"),
                    "Invoice": f"{res.get('inv_amt')} {res.get('inv_currency')}",
                    "PO": f"{res.get('po_amt')} {res.get('po_currency')}",
                    "Variance": f"{res.get('variance_pct')}%",
                    "Issue": res.get("issue_type"),
                    "Risk": res.get("risk_level"),
                    "RawData": res
                })
                show_details(res)

with tab2:
    if st.session_state.history:
        st.markdown("### Master Audit Log")
        df = pd.DataFrame(st.session_state.history)
        def color_risk(val):
            color = 'red' if 'HIGH' in str(val) else 'orange' if 'MEDIUM' in str(val) else 'green'
            return f'color: {color}; font-weight: bold'
        st.dataframe(df.drop(columns=['RawData']).style.map(color_risk, subset=['Risk']), use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV Report", csv, "audit_log.csv", "text/csv")
    else:
        st.info("Upload documents to begin.")

with tab3:
    st.markdown("### Vendor Risk Distribution")
    if st.session_state.history:
        df_viz = pd.DataFrame(st.session_state.history)
        risk_counts = df_viz['Risk'].value_counts()
        st.bar_chart(risk_counts)
    else:
        st.info("No data available yet.")
