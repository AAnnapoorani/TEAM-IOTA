import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
from datetime import datetime, timedelta

# =========================================
# CONFIGURATION
# =========================================
API_BASE = "http://127.0.0.1:8000"
REFRESH_INTERVAL = 30  # seconds
SLA_HOURS = 48  # threshold for SLA

st.set_page_config(
    page_title="Smart Grievance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .high-urgency {background-color: #ff4d4f; color: #ffffff; padding:10px; border-radius:10px;}
    .medium-urgency {background-color: #ffa940; color: #000000; padding:10px; border-radius:10px;}
    .low-urgency {background-color: #73d13d; color: #000000; padding:10px; border-radius:10px;}
    </style>
    """, unsafe_allow_html=True
)

# =========================================
# HELPER FUNCTIONS
# =========================================
def fetch_complaints():
    """Fetch complaints data from FastAPI backend"""
    try:
        res = requests.get(f"{API_BASE}/complaints")
        if res.status_code == 200:
            data = res.json()
            df = pd.DataFrame(data)
            if df.empty:
                return pd.DataFrame()

            df["created_at"] = pd.to_datetime(df["created_at"])
            df["sla_deadline"] = df["created_at"] + pd.to_timedelta(SLA_HOURS, unit="h")
            df["sla_breached"] = df["sla_deadline"] < datetime.utcnow()

            urgency_map = {"High": 90, "Medium": 60, "Low": 30}
            df["urgency_score"] = df["urgency"].map(urgency_map).fillna(0)
            return df
        else:
            st.error("❌ Could not fetch complaints.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠ API not reachable: {e}")
        return pd.DataFrame()

def update_status(complaint_id, new_status):
    """Update complaint status"""
    try:
        res = requests.post(f"{API_BASE}/complaints/{complaint_id}/update_status", json=new_status)
        if res.status_code == 200:
            st.success(f"✅ Complaint #{complaint_id} marked as {new_status}.")
        else:
            st.error(f"❌ Failed to update (status {res.status_code}).")
    except Exception as e:
        st.error(f"⚠ Error updating status: {e}")

def urgency_label(score):
    if score >= 70:
        return "🔥 High"
    elif score >= 40:
        return "🟠 Medium"
    else:
        return "🟢 Low"

# =========================================
# UI LAYOUT
# =========================================
st.title("📊 Smart Grievance Classification & Routing Dashboard")
st.caption("AI-powered monitoring panel for SGCRS system")

st.sidebar.header("⚙ Filters & Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh every 30s", value=True)
filter_dept = st.sidebar.text_input("Filter by Department")
filter_status = st.sidebar.selectbox("Filter by Status", ["All", "in_progress", "resolved", "escalated"])

# =========================================
# FETCH DATA
# =========================================
df = fetch_complaints()

if not df.empty:
    if filter_dept:
        df = df[df["department"].str.contains(filter_dept, case=False, na=False)]
    if filter_status != "All":
        df = df[df["status"] == filter_status]

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Complaints", len(df))
    col2.metric("In Progress", (df["status"] == "in_progress").sum())
    col3.metric("Resolved", (df["status"] == "resolved").sum())
    col4.metric("SLA Breached", df["sla_breached"].sum())

    # =========================================
    # URGENT ALERTS
    # =========================================
    st.subheader("🚨 Urgent Complaints (Top 5)")
    urgent_cases = df.sort_values("urgency_score", ascending=False).head(5)
    if urgent_cases.empty:
        st.info("No high-urgency complaints 🎉")
    else:
        for _, row in urgent_cases.iterrows():
            urgency_class = (
                "high-urgency" if row["urgency_score"] >= 70
                else "medium-urgency" if row["urgency_score"] >= 40
                else "low-urgency"
            )
            st.markdown(
                f"""
                <div class="{urgency_class}">
                    <b>Complaint #{row['id']}</b><br>
                    <b>Citizen:</b> {row['citizen_name']}<br>
                    <b>Department:</b> {row['department']}<br>
                    <b>Urgency:</b> {row['urgency']}<br>
                    <b>Status:</b> {row['status']}<br>
                    <b>Created:</b> {row['created_at']}<br>
                    <b>SLA Deadline:</b> {row['sla_deadline']}
                </div>
                """, unsafe_allow_html=True
            )

    # =========================================
    # MAIN TABLE
    # =========================================
    st.subheader("📋 Complaints Overview")
    df["Urgency Level"] = df["urgency_score"].apply(urgency_label)
    # Add a nicely formatted SLA Deadline column to the table
    try:
        df["SLA Deadline"] = df["sla_deadline"].dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # fallback: if conversion fails, just copy raw value
        df["SLA Deadline"] = df["sla_deadline"].astype(str)

    st.dataframe(
        df.sort_values("created_at", ascending=False)[
            ["id", "citizen_name", "department", "Urgency Level", "status", "sla_breached", "created_at", "SLA Deadline"]
        ],
        use_container_width=True
    )

    # =========================================
    # STATUS UPDATE
    # =========================================
    st.subheader("🛠 Manage Complaint Status")
    selected_id = st.number_input("Enter Complaint ID", min_value=1, step=1)
    new_status = st.selectbox("New Status", ["in_progress", "resolved", "escalated"])
    if st.button("Update Status"):
        update_status(selected_id, new_status)

    # =========================================
    # ANALYTICS
    # =========================================
    st.subheader("📈 Department & Status Analytics")
    colA, colB = st.columns(2)
    with colA:
        dept_fig = px.bar(
            df.groupby("department")["id"].count().reset_index(),
            x="department", y="id", title="Complaints per Department",
            color="department", text_auto=True
        )
        st.plotly_chart(dept_fig, use_container_width=True)

    with colB:
        status_fig = px.pie(
            df, names="status", title="Complaint Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(status_fig, use_container_width=True)

    # =========================================
    # SLA BREACH ANALYSIS
    # =========================================
    st.subheader("⏰ SLA Compliance Overview")
    sla_fig = px.bar(
        df.groupby("sla_breached")["id"].count().reset_index(),
        x="sla_breached", y="id", color="sla_breached",
        title="SLA Breach vs On-Time Complaints",
        text_auto=True,
        color_discrete_map={True: "red", False: "green"}
    )
    st.plotly_chart(sla_fig, use_container_width=True)

else:
    st.warning("⚠ No complaints found. Please seed or submit some via API.")

# =========================================
# AUTO REFRESH
# =========================================
def safe_rerun():
    """Trigger a safe rerun of the Streamlit app."""
    try:
        st.rerun()  # new unified Streamlit function
    except Exception:
        # fallback for older Streamlit versions
        try:
            params = st.query_params
            params["_refresh"] = str(time.time())
            st.query_params = params
        except Exception:
            if st.button("🔄 Refresh"):
                pass

if auto_refresh:
    time.sleep(REFRESH_INTERVAL)
    safe_rerun()
