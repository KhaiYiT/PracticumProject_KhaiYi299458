import pandas as pd
import streamlit as st
import plotly.express as px

# Page Configuration
st.set_page_config(page_title = "Summary Dashboard", layout = "wide")

# Custom Page Styling
st.markdown("""
    <style>
    /* Main Background */
    .stApp {background-color: #F7F9FC; color: #142D4E;}
    .main .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}

    /* Main Headings */
    h1, h2, h3 {color: #142D4E !important;}

    /* General Text */
    p {color: #334B63;}

    /* Hide Left Navigation Sidebar */
    section[data-testid="stSidebar"] {display: none;}

    /* Hide Sidebar Collapse Button */
    button[data-testid="stSidebarCollapseButton"] {display: none;}

    /* Hide Top Header Navigation */
    [data-testid="stHeader"] {display: none;}

    /* Welcome Banner */
    .welcome-banner {background-color: #142D4E; padding: 22px 24px; border-radius: 10px; margin-top: 15px; margin-bottom: 22px;}
    .welcome-label {color: #80DED5 !important; font-size: 13px; font-weight: 700; margin-bottom: 10px;}
    .welcome-title {color: #FFFFFF !important; font-size: 27px; font-weight: 700; margin-bottom: 10px;}
    .welcome-description {color: #E5EDF6 !important; font-size: 15px; margin-bottom: 0;}

    /* KPI Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #FFFFFF; border: 1px solid #D5E0ED; border-radius: 10px; padding: 8px;}

    /* Buttons */
    div.stButton > button {background-color: #142D4E; color: #FFFFFF !important; border: 1px solid #142D4E; border-radius: 7px; padding: 0.55rem 1rem; font-weight: 600; transition: 0.2s;}
    div.stButton > button p {color: #FFFFFF !important;}
    div.stButton > button:hover {background-color: #19A7A1; color: #FFFFFF !important; border-color: #19A7A1;}
    div.stButton > button:hover p {color: #FFFFFF !important;}

    /* Horizontal Divider */
    hr {border-color: #D5E0ED;}
    </style>
    """, unsafe_allow_html = True)

# Back to Main Menu Button
if st.button("Main Page"):
    st.switch_page("app.py")

# Read Excel File
df_co = pd.read_csv("Tracking file for drawing validate 1(Khai Yi) 1.csv", encoding="cp1252")
df_email = pd.read_excel("Request Tracking File(Santa Rosa - 2026).xlsx")

# Data Preprocessing
df_co["Received Date"] = pd.to_datetime(df_co["Received Date"], errors = "coerce")
df_co["Completion Date"] = pd.to_datetime(df_co["Completion Date"], errors = "coerce")
df_email["Originated Date"] = pd.to_datetime(df_email["Originated Date"], errors = "coerce")
df_email["Completion Date"] = pd.to_datetime(df_email["Completion Date"], errors = "coerce")

# Calculate Pending Days as the difference between received date and completion date
df_co["Pending Days"] = (df_co["Completion Date"] - df_co["Received Date"]).dt.days
df_email["Pending Days"] = (df_email["Completion Date"] - df_email["Originated Date"]).dt.days

# Dashboard Title
st.markdown("""
    <div class="welcome-banner">
        <div class="welcome-label"> WORK RECORD TRACKING SYSTEM </div>
        <div class="welcome-title"> Summary Dashboard </div>
        <div class="welcome-description"> Overview of total workload and work progress </div>
    </div>
    """, unsafe_allow_html = True)

# Prepare Available Months
co_received_months = df_co["Received Date"].dropna().dt.to_period("M")
email_received_months = df_email["Originated Date"].dropna().dt.to_period("M")

co_completed_months = df_co["Completion Date"].dropna().dt.to_period("M")
email_completed_months = df_email["Completion Date"].dropna().dt.to_period("M")

all_months = pd.concat([co_received_months, email_received_months, co_completed_months, email_completed_months]).drop_duplicates()
all_months = all_months.sort_values(ascending = False)
month_options = all_months.dt.strftime("%b %Y").tolist()

if len(month_options) == 0:
    st.warning("No request dates are available to select.")
    st.stop()

# Calculate Current Year
today = pd.Timestamp.today().normalize()
current_year = today.year
year_start = pd.Timestamp(year = current_year, month = 1, day = 1)
tomorrow = today + pd.DateOffset(days = 1)

# Calculate Accumulated Requests Received During Current Year
co_received_ytd = df_co[(df_co["Received Date"] >= year_start) & (df_co["Received Date"] < tomorrow)].shape[0]
email_received_ytd = df_email[(df_email["Originated Date"] >= year_start) & (df_email["Originated Date"] < tomorrow)].shape[0]
total_received_ytd = co_received_ytd + email_received_ytd

# Calculate Total Pending Work Across Both Datasets
co_pending = df_co["Completion Date"].isna().sum()
email_pending = df_email["Completion Date"].isna().sum()
total_pending = co_pending + email_pending

# Annual KPI Cards
col1, col2 = st.columns(2)

with col1:
    total_tis = (df_co["TIS"].fillna("").astype(str).str.strip().replace("", pd.NA).dropna().nunique())
    st.metric(label = "Total Number of TIS", value = int(total_tis), border = True)

with col2:
    st.metric(label = f"Accumulated Requests Received ({current_year})", value = int(total_received_ytd), border = True)

# Monthly Workload Trend
months = pd.date_range(start = pd.Timestamp(year = current_year, month = 1, day = 1), end = pd.Timestamp(year = current_year, month = 12, day = 1), freq = "MS")

# Count CO Requests Received Each Month
co_received_data = df_co.copy()
co_received_data["Month"] = (co_received_data["Received Date"].dt.to_period("M").dt.to_timestamp())
co_received = co_received_data.groupby("Month").size()

# Count Email Requests Received Each Month
email_received_data = df_email.copy()
email_received_data["Month"] = (email_received_data["Originated Date"].dt.to_period("M").dt.to_timestamp())
email_received = email_received_data.groupby("Month").size()

# Count CO Requests Completed Each Month
co_completed_data = df_co.dropna(subset = ["Completion Date"]).copy()
co_completed_data["Month"] = (co_completed_data["Completion Date"].dt.to_period("M").dt.to_timestamp())
co_completed_monthly = co_completed_data.groupby("Month").size()

# Count Email Requests Completed Each Month
email_completed_data = df_email.dropna(subset = ["Completion Date"]).copy()
email_completed_data["Month"] = (email_completed_data["Completion Date"].dt.to_period("M").dt.to_timestamp())
email_completed_monthly = email_completed_data.groupby("Month").size()

# Combine Monthly Numbers Into One Table
monthly_data = pd.DataFrame({"Month": months})
monthly_data["Total Requests Received"] = (monthly_data["Month"].map(co_received).fillna(0).astype(int) + monthly_data["Month"].map(email_received).fillna(0).astype(int))
monthly_data["Total Requests Completed"] = (monthly_data["Month"].map(co_completed_monthly).fillna(0).astype(int) + monthly_data["Month"].map(email_completed_monthly).fillna(0).astype(int))
monthly_data["Month Name"] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# colour
NAVY = "#162F50"
TURQUOISE = "#45E0D0"
LIGHT_BG = "#F5F7FA"

# Display Overall Monthly Workload Trend
st.subheader(f"Overall Workload Trend - {current_year}")
st.caption(f"Total requests received from January {current_year} to December {current_year} (CO request & Email request)")

monthly_chart_data = monthly_data.copy()

fig = px.line(monthly_chart_data, x = "Month Name", y = "Total Requests Received", markers = True, text = "Total Requests Received", color_discrete_sequence = ["#142D4E"])

fig.update_traces(textposition = "top center", mode = "lines+markers+text", line = dict(width = 3), marker = dict(size = 8), textfont = dict(color = "#142D4E", size = 12))
fig.update_layout(xaxis_title = "Month", yaxis_title = "", plot_bgcolor = "white", paper_bgcolor = "#F7F9FC", font = dict(color = "#142D4E"), showlegend = False)
fig.update_xaxes(categoryorder = "array", categoryarray = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
fig.update_yaxes(showticklabels = False, showgrid = False, zeroline = False, rangemode = "tozero")

st.plotly_chart(fig, use_container_width = True)
st.divider()

# Select Performance Month
selected_month_label = st.selectbox("Choose Month", month_options)
selected_month = pd.Period(pd.to_datetime(selected_month_label, format = "%b %Y"), freq = "M")

selected_month_start = selected_month.start_time
selected_month_end = (selected_month + 1).start_time

# Calculate Total Requests Received During Selected Month
co_received_this_month = df_co[(df_co["Received Date"] >= selected_month_start) & (df_co["Received Date"] < selected_month_end)].shape[0]
email_received_this_month = df_email[(df_email["Originated Date"] >= selected_month_start) & (df_email["Originated Date"] < selected_month_end)].shape[0]
total_received_this_month = co_received_this_month + email_received_this_month

# Calculate Total Requests Received During Previous Month
previous_month_start = selected_month_start - pd.DateOffset(months = 1)
co_received_last_month = df_co[(df_co["Received Date"] >= previous_month_start) & (df_co["Received Date"] < selected_month_start)].shape[0]
email_received_last_month = df_email[(df_email["Originated Date"] >= previous_month_start) & (df_email["Originated Date"] < selected_month_start)].shape[0]
total_received_last_month = co_received_last_month + email_received_last_month

# Calculate Increase or Decrease Compared to Previous Month
total_received_change = total_received_this_month - total_received_last_month

# Calculate Requests Completed During Selected Month
co_completed_this_month = df_co[(df_co["Completion Date"] >= selected_month_start) & (df_co["Completion Date"] < selected_month_end)].shape[0]
email_completed_this_month = df_email[(df_email["Completion Date"] >= selected_month_start) & (df_email["Completion Date"] < selected_month_end)].shape[0]
total_completed_this_month = co_completed_this_month + email_completed_this_month

# Calculate Monthly Completion Rate
if total_received_this_month > 0:
    completion_rate = (total_completed_this_month / total_received_this_month) * 100
else:
    completion_rate = 0

# Calculate Requests Completed During Previous Month
co_completed_last_month = df_co[(df_co["Completion Date"] >= previous_month_start) & (df_co["Completion Date"] < selected_month_start)].shape[0]
email_completed_last_month = df_email[(df_email["Completion Date"] >= previous_month_start) & (df_email["Completion Date"] < selected_month_start)].shape[0]
total_completed_last_month = co_completed_last_month + email_completed_last_month

# Calculate Completion Change Compared to Previous Month
total_completed_change = total_completed_this_month - total_completed_last_month

# Calculate Previous Month's Completion Rate
if total_received_last_month > 0:
    completion_rate_last_month = (total_completed_last_month / total_received_last_month) * 100
else:
    completion_rate_last_month = 0

# Calculate Completion Rate Change Compared to Previous Month
completion_rate_change = completion_rate - completion_rate_last_month

# Monthly KPI Cards
st.subheader(f" Workload on {selected_month_label}")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border = True):
        st.metric(label = "Total Requests Received", value = total_received_this_month, delta = f"{total_received_change:+} Requests")

with col2:
    with st.container(border = True):
        st.metric(label = "Total Requests Completed", value = total_completed_this_month, delta = f"{total_completed_change:+} Requests")

with col3:
    with st.container(border = True):
        st.metric(label = "Completion Rate", value = f"{completion_rate:.1f}%", delta = f"{completion_rate_change:+.1f} %")

# Prepare CO Data for TIS Workload
df_tis_workload = df_co.copy()
df_tis_workload["TIS"] = df_tis_workload["TIS"].fillna("").astype(str).str.strip()
df_tis_workload["Number of items"] = pd.to_numeric(df_tis_workload["Number of items"], errors = "coerce").fillna(0)
df_tis_workload["Request Date"] = df_tis_workload["Received Date"]

# Prepare Email Data for TIS Workload
df_email_tis = df_email.copy()

if "TIS" not in df_email_tis.columns:
    df_email_tis["TIS"] = ""

df_email_tis["TIS"] = df_email_tis["TIS"].fillna("").astype(str).str.strip()
df_email_tis["Number of items"] = 0
df_email_tis["Request Date"] = df_email_tis["Originated Date"]

# Combine CO and Email Requests for TIS Workload
df_tis_workload = pd.concat([df_tis_workload[["TIS", "Request Date", "Completion Date", "Number of items"]], df_email_tis[["TIS", "Request Date", "Completion Date", "Number of items"]]], ignore_index = True)

# Filter All Requests Received During Selected Month
df_tis_month = df_tis_workload[(df_tis_workload["Request Date"] >= selected_month_start) & (df_tis_workload["Request Date"] < selected_month_end) & (df_tis_workload["TIS"] != "")].copy()

col1, col2 = st.columns(2)

with col1:
    with st.container(border = True):
        st.subheader("Workload by TIS")

        if df_tis_month.empty:
            st.info(f"No requests with a TIS handler were received in {selected_month_label}.")

        else:
            tis_chart_data = (df_tis_month.groupby("TIS").agg(
                Completed=("Completion Date", lambda values: values.notna().sum()),
                Pending=("Completion Date", lambda values: values.isna().sum())).reset_index())

            tis_chart_data = tis_chart_data.sort_values("Completed", ascending = False)

            fig_tis_workload = px.bar(tis_chart_data, x = "TIS", y = ["Completed", "Pending"], barmode = "stack", text_auto = True,
                color_discrete_map = {"Completed":NAVY, "Pending":TURQUOISE},
                labels = {"value": "Total Requests", "TIS": "TIS Handler", "variable": "Request Status"})

            fig_tis_workload.update_layout(plot_bgcolor = "white", paper_bgcolor = "#F7F9FC", font = dict(color = "#142D4E"), xaxis_title = "TIS Handler", yaxis_title = "Total Requests", legend_title_text = "Request Status")
            fig_tis_workload.update_yaxes(rangemode = "tozero", dtick = 1)

            st.plotly_chart(fig_tis_workload, use_container_width = True)

with col2:
    with st.container(border = True):
        st.subheader("Work Completion Status")

        # Filter CO Requests Received During Selected Month
        df_co_month = df_co[(df_co["Received Date"] >= selected_month_start) & (df_co["Received Date"] < selected_month_end)].copy()

        # Filter Email Requests Received During Selected Month
        df_email_month = df_email[(df_email["Originated Date"] >= selected_month_start) & (df_email["Originated Date"] < selected_month_end)].copy()

        # Calculate Current Status of All Requests Received During Selected Month
        total_completed_month = (df_co_month["Completion Date"].notna().sum() + df_email_month["Completion Date"].notna().sum())
        total_pending_month = (df_co_month["Completion Date"].isna().sum() + df_email_month["Completion Date"].isna().sum())

        status_data = pd.DataFrame({"Work Status": ["Completed", "Pending"], "Total Requests": [int(total_completed_month), int(total_pending_month)]})

        fig_status = px.pie(status_data, names = "Work Status", values = "Total Requests", color = "Work Status",color_discrete_map = {"Completed": NAVY, "Pending": TURQUOISE}, hole = 0.45)
        fig_status.update_layout(paper_bgcolor = "#F7F9FC", font = dict(color = "#142D4E"), legend_title_text = "")

        st.plotly_chart(fig_status, use_container_width = True)

# Pending Work Requiring Attention
st.subheader("Pending Work Requiring Attention")

st.metric(label = "Total Pending Requests", value = int(total_pending_month), border = True)

if st.button("View Pending Requests", use_container_width = True):
    st.switch_page("pages/Pending_Work.py")

# Request Navigation
col1, col2 = st.columns(2)

with col1:
    if st.button("CO Requests", use_container_width = True):
        st.switch_page("pages/CO_Request.py")

with col2:
    if st.button("Email Requests", use_container_width = True):
        st.switch_page("pages/Email_Request.py")