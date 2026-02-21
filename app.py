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

# POP-UP (DIALOG) FOR DETAILED ANALYSIS
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

# --- SIDEBAR: SYSTEM STATS ---
with st.sidebar:
    st.header("📊 Session Intelligence")
    if st.session_state.history:
        df_stats = pd.DataFrame(st.session_state.history)
        st.metric("Total Audits", len(df_stats))
        high_risk = len(df_stats[df_stats['Risk'].str.contains("HIGH")])
        st.metric("High Risk Flags", high_risk, delta=high_risk, delta_color="inverse")
    else:
        st.write("No audits run yet.")
    
    st.divider()
    tolerance = st.slider("Variance Tolerance (%)", 0.0, 5.0, 1.0)
    st.divider()
    if st.button("Clear Session"):
        st.session_state.history = []
        st.rerun()

# --- TABS FOR BETTER SEPARATION ---
tab1, tab2, tab3 = st.tabs(["📥 Ingestion", "📋 Audit Trail", "📈 Insights"])

with tab1:
    st.markdown("### Step 1: Document Upload")
    c1, c2 = st.columns(2)
    with c1:
        po_file = st.file_uploader("Authorized Purchase Order", type="pdf")
    with c2:
        inv_file = st.file_uploader("Incoming Vendor Invoice", type="pdf")
    
    if po_file and inv_file:
        st.success("Documents Loaded Successfully.")
        if st.button("🚀 Execute Forensic Audit", use_container_width=True):
            with st.spinner('AI Agent is scanning for discrepancies...'):
                po_text = get_clean_text(po_file)
                inv_text = get_clean_text(inv_file)
                
                prompt = f"""
                Analyze these documents as a Forensic Accountant.
                1. Detect Currency & Convert to PO Currency.
                2. Check Variance. Tolerance is {tolerance}%.
                3. Identify unauthorized line items.
                4. Risk: LOW if variance < {tolerance}% & no extra items. MEDIUM if variance 1-5%. HIGH if extra items or variance > 5%.
                
                PO: {po_text}
                INV: {inv_text}
                
                Output ONLY JSON: {{vendor, inv_amt, inv_currency, po_amt, po_currency, variance_pct, risk_level, issue_type, human_review, review_reason}}
                """
                
                response = model.generate_content(prompt)
                res = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                
                # Add to History
                st.session_state.history.append({
                    "Vendor": res.get("vendor"),
                    "Invoice": f"{res.get('inv_amt')} {res.get('inv_currency')}",
                    "PO": f"{res.get('po_amt')} {res.get('po_currency')}",
                    "Variance": f"{res.get('variance_pct')}%",
                    "Issue": res.get("issue_type"),
                    "Risk": res.get("risk_level"),
                    "RawData": res # For the pop-up
                })
                
                # Trigger the Pop-up
                show_details(res)

with tab2:
    if st.session_state.history:
        st.markdown("### Master Audit Log")
        df = pd.DataFrame(st.session_state.history)
        
        # Color Coding
        def color_risk(val):
            color = 'red' if 'HIGH' in str(val) else 'orange' if 'MEDIUM' in str(val) else 'green'
            return f'color: {color}; font-weight: bold'

        st.dataframe(df.drop(columns=['RawData']).style.map(color_risk, subset=['Risk']), use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV Report", csv, "audit_log.csv", "text/csv")
    else:
        st.info("The Audit Trail will appear here after you process documents.")

with tab3:
    st.markdown("### Vendor Risk Distribution")
    if st.session_state.history:
        df_viz = pd.DataFrame(st.session_state.history)
        # Simple Bar Chart of Risks
        risk_counts = df_viz['Risk'].value_counts()
        st.bar_chart(risk_counts)
        
        st.markdown("#### Audit Notes")
        st.write("This session has identified potential leakage in the procurement cycle. Review HIGH risk vendors immediately.")
    else:
        st.info("No data available for insights yet.")
