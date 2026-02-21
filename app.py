import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
import json
from datetime import datetime

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
    if file is None: return ""
    text = "".join([p.extract_text() for p in PdfReader(file).pages])
    return text.replace('{', '[').replace('}', ']').strip()

@st.dialog("Forensic 3-Way Breakdown")
def show_details(res):
    st.markdown(f"### 🚩 Audit Result: {res.get('risk_level')}")
    st.write(f"**Root Cause:** {res.get('issue_type')}")
    st.write(f"**Detailed Reasoning:** {res.get('review_reason')}")
    st.divider()
    st.json(res)
    if st.button("Close Window"):
        st.rerun()

# --- 📱 MAIN UI ---
st.title("🕵️ Forensic 3-Way Matcher")
st.caption("Verifying PO vs. Receiving Report vs. Invoice")

with st.sidebar:
    st.header("📊 Session Intelligence")
    if st.session_state.history:
        df_stats = pd.DataFrame(st.session_state.history)
        st.metric("Total Audits", len(df_stats))
        high_risk = len(df_stats[df_stats['Risk'].str.contains("HIGH")])
        st.metric("High Risk Flags", high_risk, delta=high_risk, delta_color="inverse")
    
    st.divider()
    st.header("⚙️ Audit Policy")
    input_val = st.number_input("Tolerance %:", min_value=0.0, max_value=10.0, value=1.0, step=0.01)
    tolerance = st.slider("Slider adj:", 0.0, 10.0, value=input_val, step=0.1)
    final_policy = input_val if input_val != 1.0 else tolerance
    
    if st.button("Clear Session"):
        st.session_state.history = []
        st.rerun()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📥 Ingestion", "📋 Audit Trail", "📈 Insights"])

with tab1:
    st.markdown("### Step 1: Document Upload")
    c1, c2, c3 = st.columns(3)
    with c1:
        po_file = st.file_uploader("1. Purchase Order", type="pdf")
    with c2:
        rcv_file = st.file_uploader("2. Receiving Report", type="pdf")
    with c3:
        inv_file = st.file_uploader("3. Vendor Invoice", type="pdf")
    
    if po_file and rcv_file and inv_file:
        st.success("3-Way Document Set Loaded.")
        if st.button("🚀 Execute 3-Way Match", use_container_width=True):
            with st.spinner('Cross-referencing Order, Receipt, and Billing...'):
                po_text = get_clean_text(po_file)
                rcv_text = get_clean_text(rcv_file)
                inv_text = get_clean_text(inv_file)
                
                prompt = f"""
                Analyze these 3 documents as a Forensic Auditor.
                1. Match Quantities (Receiving vs Invoice).
                2. Match Prices (PO vs Invoice).
                3. Calculate variance % between PO Total and Invoice Total.
                
                RISK RULES:
                - LOW: Perfect match within {final_policy}% tolerance.
                - MEDIUM: Variance > {final_policy}% but < 5%.
                - HIGH: Variance > 5%, or items billed but not received.
                
                PO: {po_text}
                RCV: {rcv_text}
                INV: {inv_text}
                
                Output ONLY JSON: {{"vendor": "name", "inv_amt": 0, "variance_pct": 0, "risk_level": "LOW", "issue_type": "None", "review_reason": "reason"}}
                """
                
                response = model.generate_content(prompt)
                res = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                
                audit_entry = {
                    "Vendor": res.get("vendor"),
                    "Invoice": f"{res.get('inv_amt')}",
                    "Variance": f"{res.get('variance_pct')}%",
                    "Issue": res.get("issue_type"),
                    "Risk": res.get("risk_level"),
                    "RawData": res,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.history.append(audit_entry)
                
                if res.get("risk_level") == "LOW":
                    st.balloons()
                    st.success("✅ 3-Way Match Successful.")
                    
                    voucher_text = f"VOUCHER APPROVED: {res.get('vendor')} | {res.get('inv_amt')} | Verified by Sahir Raza Mir, MPAc"
                    st.download_button("📥 Download Voucher", voucher_text, file_name=f"voucher_{res.get('vendor')}.txt")
                else:
                    st.warning(f"⚠️ Audit Alert: {res.get('review_reason')}")
                
                show_details(res)

with tab2:
    if st.session_state.history:
        st.markdown("### Master Audit Log")
        st.info("💡 Pro Tip: Click a row to re-open the forensic breakdown.")
        
        df = pd.DataFrame(st.session_state.history)
        
        selection = st.dataframe(
            df.drop(columns=['RawData']), 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun", 
            selection_mode="single_row"
        )
        
        if len(selection.selection.rows) > 0:
            selected_idx = selection.selection.rows[0]
            show_details(st.session_state.history[selected_idx]["RawData"])
    else:
        st.info("Upload 3 documents to begin.")

with tab3:
    st.markdown("### Vendor Risk Distribution")
    if st.session_state.history:
        df_viz = pd.DataFrame(st.session_state.history)
        risk_counts = df_viz['Risk'].value_counts()
        st.bar_chart(risk_counts)
