import streamlit as st
import sqlite3
import pandas as pd
from core_engine import run_operational_audit, get_historical_resolution_suggestion

DB_FILE = "production_ops.db"

def init_production_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS operational_logs (
                                                                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                                                   filename TEXT,
                                                                   task TEXT,
                                                                   owner TEXT,
                                                                   urgency TEXT,
                                                                   confidence INTEGER,
                                                                   status TEXT DEFAULT 'Pending'
                   )
                   ''')
    conn.commit()
    conn.close()

init_production_db()
st.set_page_config(page_title="OpsPulse AI Engine", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff; }
    .warning-card { background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 5px solid #ffc107; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("⚡ OpsPulse Enterprise: Operational Report Auditor")

with st.sidebar:
    st.header("📂 Data Ingestion Layer")
    # Added explicit toggle environment switch for recruiters
    use_demo = st.toggle("✨ Recruiter Sandbox (Mock Engine Mode)", value=True, help="Enable this to review full application mechanics completely free without active API token credit charges.")

    uploaded_file = st.file_uploader("Upload Daily Ops Report", type=["xlsx", "xls", "csv", "pdf", "txt"])

    if uploaded_file is not None:
        if st.button("🚀 Process & Audit Report", use_container_width=True):
            with st.spinner("Executing Extraction Pipeline..."):
                try:
                    # Pass the selector flag right to the analysis wrapper
                    analysis_result = run_operational_audit(uploaded_file, uploaded_file.name, demo_mode=use_demo)

                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    for item in analysis_result.action_items:
                        cursor.execute('''
                                       INSERT INTO operational_logs (filename, task, owner, urgency, confidence)
                                       VALUES (?, ?, ?, ?, ?)
                                       ''', (uploaded_file.name, item.task, item.owner, item.urgency, item.confidence_score))
                    conn.commit()
                    conn.close()
                    st.success("Pipeline Analysis Complete!")
                    st.info(f"**AI Summary Output:** {analysis_result.summary}")
                except Exception as e:
                    st.error(f"Pipeline Pipeline Error: {e}")

conn = sqlite3.connect(DB_FILE)
df_active = pd.read_sql_query("SELECT * FROM operational_logs WHERE status='Pending'", conn)
conn.close()

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1: st.markdown(f"<div class='metric-card'><h4>Pending Review Items</h4><h2>{len(df_active)} Tasks</h2></div>", unsafe_allow_html=True)
with col_m2:
    high_count = len(df_active[df_active['urgency'].str.lower() == 'high']) if not df_active.empty else 0
    st.markdown(f"<div class='metric-card' style='border-left-color: #dc3545;'><h4>High Urgency Alerts</h4><h2>{high_count} Alerts</h2></div>", unsafe_allow_html=True)
with col_m3: st.markdown("<div class='metric-card' style='border-left-color: #28a745;'><h4>Avg Manual Time Reduction</h4><h2>~30% Saved</h2></div>", unsafe_allow_html=True)

st.write("\n")
st.subheader("📋 Live Automated Action Routing Queue")

if df_active.empty:
    st.info("Queue clear. No unresolved operational tasks flagged.")
else:
    for idx, row in df_active.iterrows():
        # Fixed: Explicitly set column proportions (e.g., 3:1 ratio)
        card_col, control_col = st.columns([3, 1])
        with card_col:
            if row['confidence'] <= 3:
                # Fixed: Changed unsafe_with_html to unsafe_allow_html
                st.markdown(f"<div class='warning-card'>⚠️ <b>Low Confidence Score ({row['confidence']}/5)</b>: Verify details manually.</div>", unsafe_allow_html=True)
            st.markdown(f"### **Task:** {row['task']}")
            meta1, meta2, meta3 = st.columns(3)
            with meta1: st.write(f"🏢 **Department:** `{row['owner']}`")
            with meta2: st.write(f"🚦 **Priority Level:** {row['urgency'].upper()}")
            with meta3: st.write(f"📄 **Source:** `{row['filename']}`")
            st.caption(f"🤖 *Knowledge Base Lookup:* {get_historical_resolution_suggestion(row['task'])}")
        with control_col:
            st.write("")
            if st.button("✅ Route & Resolve", key=f"resolve_{row['id']}", use_container_width=True):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE operational_logs SET status='Resolved' WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
        st.divider()
#
# else:
#     for idx, row in df_active.iterrows():
#         card_col, control_col = st.columns()
#         with card_col:
#             if row['confidence'] <= 3:
#                 st.markdown(f"<div class='warning-card'>⚠️ <b>Low Confidence Score ({row['confidence']}/5)</b>: Verify details manually.</div>", unsafe_with_html=True)
#             st.markdown(f"### **Task:** {row['task']}")
#             meta1, meta2, meta3 = st.columns(3)
#             with meta1: st.write(f"🏢 **Department:** `{row['owner']}`")
#             with meta2: st.write(f"🚦 **Priority Level:** {row['urgency'].upper()}")
#             with meta3: st.write(f"📄 **Source:** `{row['filename']}`")
#             st.caption(f"🤖 *Knowledge Base Lookup:* {get_historical_resolution_suggestion(row['task'])}")
#         with control_col:
#             st.write("")
#             if st.button("✅ Route & Resolve", key=f"resolve_{row['id']}", use_container_width=True):
#                 conn = sqlite3.connect(DB_FILE)
#                 cursor = conn.cursor()
#                 cursor.execute("UPDATE operational_logs SET status='Resolved' WHERE id=?", (row['id'],))
#                 conn.commit()
#                 conn.close()
#                 st.rerun()
#         st.divider()
