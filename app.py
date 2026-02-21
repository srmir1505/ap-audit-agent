import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
import json
import time
from datetime import datetime
from google.api_core import exceptions

# 1. PAGE CONFIG
st.set_page_config(page_title="AP Agent Pro", page_icon="🔍", layout="wide")

# --- 🔐 SECURE LOGIN GATEWAY ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.write("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>🕵️ Forensic Access</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sahir's Enterprise AP Auditor</p>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.text_input("Enter Secure Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.text_input("Enter Secure Password", type="password", on_change=password_entered, key="password")
            st.error("😕 Password incorrect. Access Denied.")
        return False
    else:
        # Password correct.
        return True

# --- 🚀 MAIN APPLICATION WRAPPER ---
if check_password():
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
        st.write(f"**Vendor:** {res.get('vendor')}")
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
        
        st.divider()
        if st.button("Log Out"):
            st.session_state["password_correct"] = False
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
                with st.spinner('Performing Forensic Audit...'):
                    po_text = get_clean_text(po_file)
                    rcv_text = get_clean_text(rcv_file)
                    inv_text = get_clean_text(inv_file)
                    
                    prompt = f"""
                    Analyze these 3 documents as a Forensic Auditor. Match Quantities and Prices.
                    PO: {po_text}
                    RCV: {rcv_text}
                    INV: {inv_text}
                    Output ONLY JSON with: vendor, inv_amt, variance_pct, risk_level, issue_type, review_reason.
                    """
                    
                    max_retries = 3
                    for i in range(max_retries):
                        try:
                            response = model.generate_content(prompt)
                            res = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                            
                            audit_entry = {
                                "Vendor": res.get("vendor"),
                                "Invoice": f"{res.get('inv_amt')}",
                                "Variance": f"{res.get('variance_pct')}%",
                                "Issue": res.get("issue_type"),
                                "Risk": res.get("risk_level"),
                                "RawData": res,
                                "Timestamp": datetime.now().strftime("%H:%M:%S")
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
                            break

                        except exceptions.ResourceExhausted:
                            if i < max_retries - 1:
                                st.warning(f"🚦 System Busy. Retrying in 10s...")
                                time.sleep(10)
                            else:
                                st.error("🛑 Daily Quota Exceeded.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                            break

    with tab2:
        if st.session_state.history:
            st.markdown("### Master Audit Log")
            df = pd.DataFrame(st.session_state.history)
            audit_options = [f"{item['Vendor']} ({item['Timestamp']})" for item in st.session_state.history]
            
            selected_audit_name = st.selectbox("Select an audit to review:", options=audit_options, index=len(audit_options)-1)
            if st.button("🔎 View Breakdown", use_container_width=True):
                idx = audit_options.index(selected_audit_name)
                show_details(st.session_state.history[idx]["RawData"])

            st.divider()
            st.dataframe(df.drop(columns=['RawData']), use_container_width=True, hide_index=True)
        else:
            st.info("The Audit Trail will appear here after you process documents.")

    with tab3:
        st.markdown("### Vendor Risk Distribution")
        if st.session_state.history:
            df_viz = pd.DataFrame(st.session_state.history)
            risk_counts = df_viz['Risk'].value_counts()
            st.bar_chart(risk_counts)
