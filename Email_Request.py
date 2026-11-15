import pandas as pd
import streamlit as st
import plotly.express as px

# Convert PL and ER codes into text values
# This keeps numeric-looking codes categorical (e.g. 12, 53, B1)
def clean_code(value):
    if pd.isna(value):
        return ""

    code = str(value).strip()

    # Remove an unnecessary decimal suffix without changing text codes
    # (e.g. 12.0 becomes 12, while 01 and B1 remain unchanged)
    if code.endswith(".0") and code[:-2].isdigit():
        code = code[:-2]

    return code

# Page Configuration
st.set_page_config(page_title="Email Request", layout="wide")

# Custom Page Styling
st.markdown("""
<style>
    .stApp {background-color: #F7F9FC; color: #142D4E;}
    .main .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}
    h1, h2, h3 {color: #142D4E !important;}
    p {color: #334B63;}
    section[data-testid="stSidebar"] {display: none;}
    button[data-testid="stSidebarCollapseButton"] {display: none;}
    [data-testid="stHeader"] {display: none;}
    .welcome-banner {
        background-color: #142D4E;
        padding: 22px 24px;
        border-radius: 10px;
        margin-top: 15px;
        margin-bottom: 22px;
    }

    .welcome-label {
        color: #80DED5 !important;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .welcome-title {
        color: #FFFFFF !important;
        font-size: 27px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .welcome-description {
        color: #E5EDF6 !important;
        font-size: 15px;
        margin-bottom: 0;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #D5E0ED;
        border-radius: 10px;
        padding: 8px;
    }

    div.stButton > button {
        background-color: #142D4E;
        color: #FFFFFF !important;
        border: 1px solid #142D4E;
        border-radius: 7px;
        padding: 0.55rem 1rem;
        font-weight: 600;
        transition: 0.2s;
    }

    div.stButton > button p {
        color: #FFFFFF !important;
    }

    div.stButton > button:hover {
        background-color: #19A7A1;
        color: #FFFFFF !important;
        border-color: #19A7A1;
    }

    div.stButton > button:hover p {
        color: #FFFFFF !important;
    }

    hr {
        border-color: #D5E0ED;
    }
</style>
""", unsafe_allow_html=True)

# Back to Main Page Button
if st.button("Main Page"):
    st.switch_page("app.py")

# Read Email Excel File
@st.cache_data
def load_email_data():

    df = pd.read_excel("Request Tracking File(Santa Rosa - 2026).xlsx")

    # Standardize column headings
    df.columns = [str(col).strip() for col in df.columns]

    # Support alternative column names
    rename_columns = {}

    for col in df.columns:
        key = col.strip().lower()

        if key in ["no", "email no", "email id", "unique id"]:
            rename_columns[col] = "No"
        elif key in ["pl", "pl name"]:
            rename_columns[col] = "PL"
        elif key in ["er", "er name"]:
            rename_columns[col] = "ER"
        elif key in ["npi", "npi name"]:
            rename_columns[col] = "NPI Name"
        elif key in ["originated date", "origin date", "received date"]:
            rename_columns[col] = "Originated Date"
        elif key == "completed date":
            rename_columns[col] = "Completion Date"
        elif key in ["remarks", "remarks (if any)"]:
            rename_columns[col] = "Remarks"
        elif key in ["co/cr/inr/email", "co / cr / inr / email", "co-cr-inr-email", "reference", "reference no", "reference number"]:
            rename_columns[col] = "CO/CR/INR/Email"

    df = df.rename(columns=rename_columns)

    # Remove duplicate column names after renaming
    df = df.loc[:, ~df.columns.duplicated()]

    # Remarks and reference are optional
    if "Remarks" not in df.columns:
        df["Remarks"] = ""

    if "CO/CR/INR/Email" not in df.columns:
        df["CO/CR/INR/Email"] = ""

    # Check Required Columns
    required_columns = ["No", "TIS", "PL", "ER", "NPI Name", "Requestor", "Originated Date", "Completion Date"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing Excel columns: " + ", ".join(missing_columns)
        )

    # Data Preprocessing
    df["Originated Date"] = pd.to_datetime(df["Originated Date"], errors="coerce")
    df["Completion Date"] = pd.to_datetime(df["Completion Date"], errors="coerce")

    text_columns = ["No", "TIS", "PL", "ER", "NPI Name", "Requestor", "CO/CR/INR/Email", "Remarks"]

    for col in text_columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Keep PL and ER as categorical text codes
    df["PL"] = df["PL"].apply(clean_code)
    df["ER"] = df["ER"].apply(clean_code)

    # Determine Work Status from Completion Date
    df["Status"] = df["Completion Date"].apply(lambda x: "Completed" if pd.notna(x) else "Pending")

    # Calculate Pending Days for outstanding requests
    today = pd.Timestamp.today().normalize()
    df["Pending Days"] = (today - df["Originated Date"]).dt.days.where(df["Completion Date"].isna())

    return df

try:
    df_email = load_email_data()
except Exception as e:
    st.error(f"Unable to load the Email Excel file: {e}")
    st.exception(e)
    st.stop()


# Dashboard Title
st.markdown("""
<div class="welcome-banner">
    <div class="welcome-label"> WORK RECORD TRACKING SYSTEM </div>
    <div class="welcome-title"> Email Request Dashboard </div>
    <div class="welcome-description"> Analyse Email workload, request handling, processing time, and pending requests </div>
</div>
""", unsafe_allow_html=True)


# Introduction
st.subheader("Why an Email Request is needed?")

with st.container(border=True):
    st.write("An Email Request is used to record and monitor requests received through email, including the assigned TIS, PL and ER, the related NPI, requestor, and request progress.")

st.divider()

# Prepare Available Months
originated_months = df_email["Originated Date"].dropna().dt.to_period("M")
completed_months = df_email["Completion Date"].dropna().dt.to_period("M")

all_months = pd.concat([originated_months, completed_months], ignore_index=True).drop_duplicates().sort_values(ascending=False)
month_options = all_months.dt.strftime("%b-%Y").tolist()

if len(month_options) == 0:
    st.warning("No valid Email Request dates are available.")
    st.stop()

# Overview (accumulated for the current year)
today = pd.Timestamp.today().normalize()

current_year = today.year
year_start = pd.Timestamp(year=current_year, month=1, day=1)
next_year_start = pd.Timestamp(year=current_year + 1, month=1, day=1)

df_email_year = df_email[(df_email["Originated Date"] >= year_start) & (df_email["Originated Date"] < next_year_start)].copy()

df_email_completed_year = df_email[(df_email["Completion Date"] >= year_start) & (df_email["Completion Date"] < next_year_start)].copy()

annual_email_received = len(df_email_year)
annual_email_completed = len(df_email_completed_year)

st.subheader(f"Overview - {current_year}")

annual_col1, annual_col2 = st.columns(2)

with annual_col1:
    with st.container(border=True):
        st.metric(label=f"Accumulated Email Requests Received in {current_year}", value=annual_email_received)

with annual_col2:
    with st.container(border=True):
        st.metric(label=f"Accumulated Email Requests Completed in {current_year}", value=annual_email_completed)

st.divider()

# Select Month (shown after the Annual Overview)
selected_month_label = st.selectbox("Select Month", month_options)
selected_month = pd.Period(pd.to_datetime(selected_month_label, format="%b-%Y"), freq="M")
selected_month_start = selected_month.start_time
selected_month_end = (selected_month + 1).start_time
previous_month_start = selected_month_start - pd.DateOffset(months=1)

# Records received during the selected month (used for month-based analysis)
df_email_month = df_email[(df_email["Originated Date"] >= selected_month_start) & (df_email["Originated Date"] < selected_month_end)].copy()

# Monthly Overview KPIs
monthly_email_received = len(df_email_month)
monthly_email_pending = int(df_email_month["Completion Date"].isna().sum())

# Calculate Email Requests Received During Selected Month
email_received_this_month = df_email[(df_email["Originated Date"] >= selected_month_start) & (df_email["Originated Date"] < selected_month_end)].shape[0]

# Calculate Email Requests Received During Previous Month
email_received_last_month = df_email[(df_email["Originated Date"] >= previous_month_start) & (df_email["Originated Date"] < selected_month_start)].shape[0]
email_received_change = (email_received_this_month - email_received_last_month)

# Calculate Email Requests Completed During Selected Month
email_completed_this_month = df_email[(df_email["Completion Date"] >= selected_month_start) & (df_email["Completion Date"] < selected_month_end)].shape[0]

# Calculate Email Requests Completed During Previous Month
email_completed_last_month = df_email[(df_email["Completion Date"] >= previous_month_start) & (df_email["Completion Date"] < selected_month_start)].shape[0]
email_completed_change = (email_completed_this_month - email_completed_last_month)

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.metric(label="Email Requests Received", value=int(email_received_this_month), delta=f"{email_received_change:+} Requests")

with col2:
    with st.container(border=True):
        st.metric(label="Email Requests Completed", value=int(email_completed_this_month), delta=f"{email_completed_change:+} Requests")

with col3:
    with st.container(border=True):
        st.metric(label="Current Pending Emails", value=monthly_email_pending)
        if st.button("View Pending", use_container_width=True):
            st.switch_page("pages/Pending_Work.py")

with st.container(border=True):
    st.subheader(f"Email Request Trend in {selected_month.strftime('%b-%Y')}")

    # Get all days in the selected month
    days_in_month = selected_month.days_in_month
    daily_data = pd.DataFrame({"Day": range(1, days_in_month + 1)})

    # Count Email requests received each day
    received_data = df_email[(df_email["Originated Date"] >= selected_month_start) & (df_email["Originated Date"] < selected_month_end)].copy()
    received_data["Day"] = received_data["Originated Date"].dt.day
    received_daily = received_data.groupby("Day").size()

    # Count Email requests completed each day
    completed_data = df_email[(df_email["Completion Date"] >= selected_month_start) & (df_email["Completion Date"] < selected_month_end)].copy()
    completed_data["Day"] = completed_data["Completion Date"].dt.day
    completed_daily = completed_data.groupby("Day").size()

    # Add daily totals to the chart data
    daily_data["Email Received"] = daily_data["Day"].map(received_daily).fillna(0).astype(int)
    daily_data["Email Completed"] = daily_data["Day"].map(completed_daily).fillna(0).astype(int)

    # Convert data for the line chart
    daily_chart_data = daily_data.melt(id_vars=["Day"], value_vars=["Email Received", "Email Completed"], var_name="Work Status", value_name="Number of Emails")

    # Create daily Email Received line chart
    fig_trend = px.line(daily_data, x="Day", y="Email Received", markers=False, text="Email Received", color_discrete_sequence=["#142D4E"])
    fig_trend.update_traces(textposition="top center", hovertemplate="Day %{x}<br> Email Received: %{y}<extra></extra>")
    fig_trend.update_layout(xaxis_title="Day of Month", yaxis_title="Number of Email Requests Received", plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False)
    fig_trend.update_xaxes(tickmode="linear", tick0=1, dtick=1, range=[0.5, days_in_month + 0.5])
    fig_trend.update_yaxes(rangemode="tozero", dtick=1)

    st.plotly_chart(fig_trend, use_container_width=True)



# Analysis Section
st.divider()
with st.expander("View Monthly Analysis (Click to expand)", expanded=False):
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            requestor_data = df_email_month.copy()
            requestor_data["Requestor"] = requestor_data["Requestor"].replace("", "Unspecified")
            requestor_summary = (requestor_data.groupby("Requestor", as_index=False).agg(Total_Requests=("Originated Date", "size")).sort_values("Total_Requests", ascending=False))

            top_requestors = requestor_summary.head(10).sort_values("Total_Requests", ascending=True)

            st.subheader("Requestor Analysis")

            fig_requestors = px.bar(top_requestors, x="Total_Requests", y="Requestor", orientation="h", text="Total_Requests", color_discrete_sequence=["#193653"])
            fig_requestors.update_traces(textposition="outside", hovertemplate="<b>%{y}</b><br>Email Requests: %{x}<extra></extra>")
            fig_requestors.update_layout(xaxis_title="Number of Email Requests", yaxis_title="", plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False, margin=dict(l=10, r=25, t=15, b=10))
            fig_requestors.update_xaxes(rangemode="tozero", dtick=1)

            st.caption(f"Top 10 requestors in {selected_month_label}.")
            st.plotly_chart(fig_requestors, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.subheader("Product Line (PL) Analysis")

            # Clean PL values as categorical Product Line codes
            pl_data = df_email_month.copy()
            pl_data["PL"] = pl_data["PL"].apply(clean_code).replace("", "Unassigned")

            # Summarise Email requests by Product Line
            pl_summary = (pl_data.groupby("PL").size().reset_index(name="Total Requests").sort_values("Total Requests", ascending=False))

            # Product Line (PL) Treemap
            if not pl_summary.empty:
                fig_pl = px.treemap(pl_summary, path=["PL"], values="Total Requests", color="Total Requests", color_continuous_scale=["#D9F5E8", "#248F95", "#193653"])
                fig_pl.update_traces(textinfo="label+percent parent", hovertemplate="<b>PL: %{label}</b><br>Email Requests: %{value}<br>Percentage: %{percentRoot}<extra></extra>")
                fig_pl.update_layout(plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), coloraxis_showscale=False, margin=dict(l=10, r=10, t=15, b=10))

                st.caption("Distribution of Email Requests by Product Line")
                st.plotly_chart(fig_pl, use_container_width=True)
            else:
                st.info(f"No PL records are available in {selected_month_label}.")

    with col3:
        with st.container(border=True):
            st.subheader("Organization (ER Code) Analysis")

            # Clean ER values as categorical Organization Codes
            er_data = df_email_month.copy()
            er_data["ER"] = er_data["ER"].apply(clean_code).replace("", "Unassigned")

            # Summarise Email requests by ER
            er_summary = (er_data.groupby("ER").size().reset_index(name="Total Requests").sort_values("Total Requests", ascending=False).head(10))

            # Create vertical bar chart for ER workload
            if not er_summary.empty:
                fig_er = px.bar(er_summary, x="ER", y="Total Requests", text="Total Requests", color_discrete_sequence=["#193653"])

                fig_er.update_traces(textposition="outside", hovertemplate="<b>ER Code: %{x}</b><br>Email Requests: %{y}<extra></extra>")
                fig_er.update_layout(xaxis_title="Organization Code (ER)", yaxis_title="Number of Email Requests", plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False, margin=dict(l=10, r=20, t=20, b=10))
                fig_er.update_yaxes(rangemode="tozero", dtick=1)
                fig_er.update_xaxes(type="category")

                st.caption("Distribution of Email Requests by Organization Code")
                st.plotly_chart(fig_er, use_container_width=True)
            else:
                st.info(f"No ER records are available in {selected_month_label}.")

    col4, col5 = st.columns(2)

    with col4:
        with st.container(border=True):
            st.subheader("TIS Workload")

            # Filter records for the selected month
            tis_data = df_email_month.copy()
            tis_data["TIS"] = tis_data["TIS"].replace("", "Unassigned")

            # Summarise Email requests by TIS and status
            tis_summary = (tis_data.groupby(["TIS", "Status"], as_index=False).agg(Total_Requests=("Originated Date", "size")))

            # Fixed colour for each TIS
            tis_colours = {"Sok Fuen":"#193653", "Pei Ling":"#248F95", "Elaine":"#65BDB7", "Ai Mei":"#D9B568", "Khai Yi":"#D78370"}

            # Give any new TIS a consistent fallback colour
            default_tis_colour = "#9B8AC4"

            all_tis = sorted(tis_summary["TIS"].unique())

            for tis in all_tis:
                if tis not in tis_colours:
                    tis_colours[tis] = default_tis_colour

            tis_chart_data = tis_summary.groupby("TIS", as_index=False)["Total_Requests"].sum()

            fig_tis = px.pie(tis_chart_data, names="TIS", values="Total_Requests", color="TIS", color_discrete_map=tis_colours, hole=0.45)
            fig_tis.update_traces(textinfo="label+percent", textposition="inside",
                                hovertemplate=("<b>TIS: %{label}</b>"
                                                "<br>Email Requests: %{value}"
                                                "<br>Percentage: %{percent}"
                                                "<extra></extra>"),)

            fig_tis.update_layout(plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False)

            st.caption("The Distribution of Email Workload for TIS")
            st.plotly_chart(fig_tis, use_container_width=True)

    with col5:
        with st.container(border=True):
            st.subheader("Top 10 Busiest NPI")

            # Count Email requests for each NPI Name
            npi_data = df_email_month.copy()

            # Clean NPI Name values
            npi_data["NPI Name"] = (npi_data["NPI Name"].fillna("").astype(str).str.strip())

            # Exclude blank NPI names
            npi_data = npi_data[npi_data["NPI Name"] != ""]

            # Calculate total Email requests for each NPI
            npi_summary = (npi_data.groupby("NPI Name").size().reset_index(name="Total Requests").sort_values("Total Requests", ascending=False).head(10))

            # Create NPI column chart
            if not npi_summary.empty:
                fig_npi = px.bar(npi_summary, x="NPI Name", y="Total Requests", text="Total Requests", color_discrete_sequence=["#65BDB7"])

                fig_npi.update_traces(textposition="outside", hovertemplate="<b>%{x}</b><br>Email Requests: %{y}<extra></extra>")
                fig_npi.update_layout(xaxis_title="NPI Name", yaxis_title="Number of Email Requests", plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False, margin=dict(l=10, r=20, t=20, b=10))
                fig_npi.update_yaxes(rangemode="tozero", dtick=1)
                fig_npi.update_xaxes(tickangle=-45)

                st.plotly_chart(fig_npi, use_container_width=True)
            else:
                st.info(f"No NPI records are available in {selected_month_label}.")

# Email Record Management (Subsystem)
st.divider()
st.subheader("Email Record Management")

file_path = "Request Tracking File(Santa Rosa - 2026).xlsx"
action = st.radio("Select Action", ["Add New Record", "Update Existing Record", "Delete Email Record", "Search Email Records"], horizontal=True, key="email_management_action")

try:
    df_existing = pd.read_excel(file_path)

    # Match the actual column names in your Excel file
    df_existing.columns = [str(col).strip() for col in df_existing.columns]

    # Identify the actual Excel column names
    email_rename_columns = {}

    for col in df_existing.columns:
        key = col.strip().lower()

        if key in ["no", "email no", "email id", "unique id"]:
            email_rename_columns[col] = "No"
        elif key in ["pl", "pl name"]:
            email_rename_columns[col] = "PL"
        elif key in ["er", "er name"]:
            email_rename_columns[col] = "ER"
        elif key in ["npi", "npi name"]:
            email_rename_columns[col] = "NPI Name"
        elif key in ["originated date", "origin date", "received date"]:
            email_rename_columns[col] = "Originated Date"
        elif key == "completed date":
            email_rename_columns[col] = "Completion Date"
        elif key in ["remarks", "remarks (if any)"]:
            email_rename_columns[col] = "Remarks"
        elif key in ["co/cr/inr/email", "co / cr / inr / email", "co-cr-inr-email", "reference", "reference no", "reference number"]:
            email_rename_columns[col] = "CO/CR/INR/Email"

    df_existing = df_existing.rename(columns=email_rename_columns)
    df_existing = df_existing.loc[:, ~df_existing.columns.duplicated()]

    # Add optional columns if they do not exist
    for col in ["Remarks", "CO/CR/INR/Email"]:
        if col not in df_existing.columns:
            df_existing[col] = ""

    required_columns = ["No", "TIS", "PL", "ER", "NPI Name", "Requestor", "Originated Date", "Completion Date"]
    missing_columns = [col for col in required_columns if col not in df_existing.columns]

    if missing_columns:
        raise ValueError("Missing Excel columns: " + ", ".join(missing_columns))

    # Prepare record management data
    df_existing["Originated Date"] = pd.to_datetime(df_existing["Originated Date"], errors="coerce")
    df_existing["Completion Date"] = pd.to_datetime(df_existing["Completion Date"], errors="coerce")

    for col in ["No", "TIS", "PL", "ER", "NPI Name", "Requestor", "CO/CR/INR/Email", "Remarks"]:
        df_existing[col] = df_existing[col].fillna("").astype(str).str.strip()

    # Keep PL and ER as categorical text codes
    df_existing["PL"] = df_existing["PL"].apply(clean_code)
    df_existing["ER"] = df_existing["ER"].apply(clean_code)

    # Create readable record labels for update and delete
    def get_email_record_label(row_index, record):
        originated_date = record["Originated Date"].strftime("%d-%b-%Y") if pd.notna(record["Originated Date"]) else "No Date"
        email_no = record.get("No", "")
        reference = record.get("CO/CR/INR/Email", "")
        npi_name = record.get("NPI Name", "")
        requestor = record.get("Requestor", "")
        return f"{email_no} | {reference} | {npi_name} | {requestor} | {originated_date}"

    email_record_options = {
        get_email_record_label(row_index, record): row_index
        for row_index, record in df_existing.iterrows()
    }

        # Add New Email Record
    if action == "Add New Record":
            with st.form("add_email_record_form", clear_on_submit=True):

                col1, col2 = st.columns(2)
                with col1:
                    email_no = st.text_input("No (Unique Email ID)")
                    tis = st.text_input("TIS (Assigned by?)")
                    pl = st.text_input("PL")
                    er = st.text_input("ER")
                    ibo = st.text_input("IBO")
                    dept_wsf = st.text_input("Dept_WSF")
                    category_of_change = st.text_input("Category of Change")

                with col2:
                    reference = st.text_input("CO/CR/INR/Email Reference")
                    npi_name = st.text_input("NPI Name")
                    requestor = st.text_input("Requestor")
                    change_details = st.text_input("Change Details")
                    originated_date = st.date_input("Originated Date")
                    remarks = st.text_area("Remarks (Optional)")
                    has_completion_date = st.checkbox("Email Request already completed")

                    if has_completion_date:
                        completion_date = st.date_input("Completion Date")
                    else:
                        completion_date = None

                submitted = st.form_submit_button("Save Email Record", use_container_width=True)

                if submitted:
                    if not all([email_no.strip(), tis.strip(), pl.strip(), er.strip(), npi_name.strip(), requestor.strip()]):
                        st.error("Please fill in No, TIS, PL, ER, NPI Name and Requestor")
                    else:
                        try:
                            # Read the existing Excel file
                            df_latest = pd.read_excel(file_path)
                            df_latest.columns = [str(col).strip() for col in df_latest.columns]

                            latest_rename_columns = {}
                            for col in df_latest.columns:
                                key = col.strip().lower()
                                if key in ["no", "email no", "email id", "unique id"]:
                                    latest_rename_columns[col] = "No"
                                elif key in ["pl", "pl name"]:
                                    latest_rename_columns[col] = "PL"
                                elif key in ["er", "er name"]:
                                    latest_rename_columns[col] = "ER"
                                elif key in ["npi", "npi name"]:
                                    latest_rename_columns[col] = "NPI Name"
                                elif key in ["originated date", "origin date", "received date"]:
                                    latest_rename_columns[col] = "Originated Date"
                                elif key == "completed date":
                                    latest_rename_columns[col] = "Completion Date"
                                elif key in ["remarks", "remarks (if any)"]:
                                    latest_rename_columns[col] = "Remarks"
                                elif key in ["co/cr/inr/email", "co / cr / inr / email", "co-cr-inr-email", "reference", "reference no", "reference number"]:
                                    latest_rename_columns[col] = "CO/CR/INR/Email"

                            df_latest = df_latest.rename(columns=latest_rename_columns)
                            df_latest = df_latest.loc[:, ~df_latest.columns.duplicated()]

                            if "No" not in df_latest.columns:
                                st.error("The Excel file must contain a 'No' column for the unique Email ID.")
                                st.stop()

                            existing_email_nos = df_latest["No"].fillna("").astype(str).str.strip().str.casefold()
                            if email_no.strip().casefold() in existing_email_nos.values:
                                st.error(f"Email ID '{email_no}' already exists. Please enter a different unique ID.")
                                st.stop()

                            for col in ["IBO", "Dept_WSF", "Category of Change", "Change Details", "Remarks", "CO/CR/INR/Email"]:
                                if col not in df_latest.columns:
                                    df_latest[col] = ""

                            # Prepare the new record
                            new_record = {
                                "No": email_no.strip(),
                                "TIS": tis.strip(),
                                "PL": pl.strip(),
                                "ER": er.strip(),
                                "IBO": ibo.strip(),
                                "Dept_WSF": dept_wsf.strip(),
                                "Category of Change": category_of_change.strip(),
                                "CO/CR/INR/Email": reference.strip(),
                                "NPI Name": npi_name.strip(),
                                "Requestor": requestor.strip(),
                                "Change Details": change_details.strip(),
                                "Originated Date": pd.to_datetime(originated_date),
                                "Completion Date": (pd.to_datetime(completion_date)
                                                     if completion_date is not None
                                                     else pd.NaT),
                                "Remarks": remarks.strip()
                            }

                            # Add the new record without replacing existing records
                            df_updated = pd.concat([df_latest, pd.DataFrame([new_record])], ignore_index=True)

                            # Save the updated Excel file
                            df_updated.to_excel(file_path, index=False)
                            load_email_data.clear()
                            st.success("Email Record added successfully!")
                            st.rerun()

                        except PermissionError:
                            st.error("Cannot save the Excel file. Please close it in Excel and try again.")

                        except Exception as e:
                            st.error(f"Unable to save the Email record: {e}")

    # Update Existing Email Record
    elif action == "Update Existing Record":
            if df_existing.empty:
                st.info("There are no Email records available to update.")

            else:
                selected_email_no = st.text_input("Enter No to update", placeholder="Type the unique Email No (e.g., 5060)", key="update_email_no").strip()

                if selected_email_no:
                    selected_rows = df_existing[df_existing["No"].astype(str).str.strip().str.casefold() == selected_email_no.casefold()]
                else:
                    selected_rows = df_existing.iloc[0:0]

                if selected_rows.empty and selected_email_no:
                    st.warning(f"No Email record found with No '{selected_email_no}'.")
                elif not selected_rows.empty:
                    record = selected_rows.iloc[0]

                    current_email_no = str(record.get("No", "")) if pd.notna(record.get("No")) else ""
                    current_tis = str(record.get("TIS", "")) if pd.notna(record.get("TIS")) else ""
                    current_pl = str(record.get("PL", "")) if pd.notna(record.get("PL")) else ""
                    current_er = str(record.get("ER", "")) if pd.notna(record.get("ER")) else ""
                    current_ibo = str(record.get("IBO", "")) if pd.notna(record.get("IBO")) else ""
                    current_dept_wsf = str(record.get("Dept_WSF", "")) if pd.notna(record.get("Dept_WSF")) else ""
                    current_category_of_change = str(record.get("Category of Change", "")) if pd.notna(record.get("Category of Change")) else ""
                    current_reference = str(record.get("CO/CR/INR/Email", "")) if pd.notna(record.get("CO/CR/INR/Email")) else ""
                    current_npi = str(record.get("NPI Name", "")) if pd.notna(record.get("NPI Name")) else ""
                    current_requestor = str(record.get("Requestor", "")) if pd.notna(record.get("Requestor")) else ""
                    current_change_details = str(record.get("Change Details", "")) if pd.notna(record.get("Change Details")) else ""
                    current_originated_date = pd.to_datetime(record["Originated Date"]).date() if pd.notna(record.get("Originated Date")) else pd.Timestamp.today().date()
                    current_completion_date = pd.to_datetime(record["Completion Date"]).date() if pd.notna(record.get("Completion Date")) else None
                    current_remarks = str(record.get("Remarks", "")) if pd.notna(record.get("Remarks")) else ""

                    with st.form("update_email_record_form"):
                        st.caption(f"Updating Email Record: {current_email_no}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.text_input("No (Unique Email ID)", value=current_email_no, disabled=True)
                            tis = st.text_input("TIS (Assigned by?)", value=current_tis)
                            pl = st.text_input("PL", value=current_pl)
                            er = st.text_input("ER", value=current_er)
                            ibo = st.text_input("IBO", value=current_ibo)
                            dept_wsf = st.text_input("Dept_WSF", value=current_dept_wsf)
                            category_of_change = st.text_input("Category of Change", value=current_category_of_change)

                        with col2:
                            reference = st.text_input("CO/CR/INR/Email Reference", value=current_reference)
                            npi_name = st.text_input("NPI Name", value=current_npi)
                            requestor = st.text_input("Requestor", value=current_requestor)
                            change_details = st.text_input("Change Details", value=current_change_details)
                            originated_date = st.date_input("Originated Date", value=current_originated_date)
                            has_completion_date = st.checkbox("Email Request completed", value=current_completion_date is not None)

                            if has_completion_date:
                                completion_date = st.date_input("Completion Date",
                                    value=(current_completion_date
                                           if current_completion_date is not None
                                           else pd.Timestamp.today().date())
                                )
                            else:
                                completion_date = None

                        remarks = st.text_area("Remarks (Optional)", value=current_remarks)
                        submitted = st.form_submit_button("Update Email Record", use_container_width=True)

                        if submitted:
                            if not all([tis.strip(), pl.strip(), er.strip(), npi_name.strip(), requestor.strip()]):
                                st.error("Please fill in TIS, PL, ER, NPI Name and Requestor")
                            else:
                                try:
                                    # Reload the file before updating
                                    df_latest = pd.read_excel(file_path)
                                    df_latest.columns = [str(col).strip() for col in df_latest.columns]

                                    # Identify the actual column names
                                    latest_rename_columns = {}
                                    for col in df_latest.columns:
                                        key = col.strip().lower()
                                        if key in ["no", "email no", "email id", "unique id"]:
                                            latest_rename_columns[col] = "No"
                                        elif key in ["pl", "pl name"]:
                                            latest_rename_columns[col] = "PL"
                                        elif key in ["er", "er name"]:
                                            latest_rename_columns[col] = "ER"
                                        elif key in ["npi", "npi name"]:
                                            latest_rename_columns[col] = "NPI Name"
                                        elif key in ["originated date", "origin date", "received date"]:
                                            latest_rename_columns[col] = "Originated Date"
                                        elif key == "completed date":
                                            latest_rename_columns[col] = "Completion Date"
                                        elif key in ["remarks", "remarks (if any)"]:
                                            latest_rename_columns[col] = "Remarks"
                                        elif key in ["co/cr/inr/email", "co / cr / inr / email", "co-cr-inr-email", "reference", "reference no", "reference number"]:
                                            latest_rename_columns[col] = "CO/CR/INR/Email"

                                    df_latest = df_latest.rename(columns=latest_rename_columns)
                                    df_latest = df_latest.loc[:, ~df_latest.columns.duplicated()]

                                    latest_matching_rows = df_latest["No"].fillna("").astype(str).str.strip().str.casefold() == current_email_no.casefold()
                                    if latest_matching_rows.any():
                                        latest_row_index = df_latest.index[latest_matching_rows][0]
                                    else:
                                        st.warning("This Email record could not be found. Please refresh and try again.")
                                        st.stop()

                                    df_latest.loc[latest_row_index, "TIS"] = tis.strip()
                                    df_latest.loc[latest_row_index, "PL"] = pl.strip()
                                    df_latest.loc[latest_row_index, "ER"] = er.strip()
                                    df_latest.loc[latest_row_index, "IBO"] = ibo.strip()
                                    df_latest.loc[latest_row_index, "Dept_WSF"] = dept_wsf.strip()
                                    df_latest.loc[latest_row_index, "Category of Change"] = category_of_change.strip()
                                    if "CO/CR/INR/Email" not in df_latest.columns:
                                        df_latest["CO/CR/INR/Email"] = ""
                                    df_latest.loc[latest_row_index, "CO/CR/INR/Email"] = reference.strip()
                                    df_latest.loc[latest_row_index, "NPI Name"] = npi_name.strip()
                                    df_latest.loc[latest_row_index, "Requestor"] = requestor.strip()
                                    df_latest.loc[latest_row_index, "Change Details"] = change_details.strip()
                                    df_latest.loc[latest_row_index, "Originated Date"] = pd.to_datetime(originated_date)
                                    df_latest.loc[latest_row_index, "Completion Date"] = (pd.to_datetime(completion_date)
                                                                                           if completion_date is not None
                                                                                           else pd.NaT)
                                    if "Remarks" not in df_latest.columns:
                                        df_latest["Remarks"] = ""
                                    df_latest.loc[latest_row_index, "Remarks"] = remarks.strip()

                                    # Save the updated Excel file
                                    df_latest.to_excel(file_path, index=False)
                                    load_email_data.clear()
                                    st.success(f"Email Record '{current_email_no}' updated successfully!")
                                    st.rerun()

                                except PermissionError:
                                    st.error("Cannot save the Excel file. Please close it in Excel and try again.")

                                except Exception as e:
                                    st.error(f"Unable to update the Email record: {e}")

        # Delete Email Record
    elif action == "Delete Email Record":
            if df_existing.empty:
                st.info("There are no Email records to delete.")

            else:
                with st.form("search_delete_email_form"):
                    search_delete_no = st.text_input("Search Email Record by No", placeholder="Enter Email No (e.g., 5060)")
                    search_delete_submitted = st.form_submit_button("Search", use_container_width=True)

                if search_delete_submitted:
                    st.session_state["searched_delete_email_no"] = search_delete_no.strip()

                selected_email_no = st.session_state.get("searched_delete_email_no", "")

                if selected_email_no:
                    selected_record = df_existing[
                        df_existing["No"].astype(str).str.strip().str.casefold() == selected_email_no.casefold()
                    ]

                    if not selected_record.empty:
                        record = selected_record.iloc[0]

                        st.success(f"Email record '{selected_email_no}' found.")

                        st.write("**Please check this record before deleting:**")
                        st.dataframe(selected_record, use_container_width=True, hide_index=True)

                        confirm_delete = st.checkbox("Confirm Delete this Email record", key=f"confirm_delete_email_{selected_email_no}")

                        if st.button("Delete Email Record", type="primary", disabled=not confirm_delete, key="delete_email_button"):
                            try:
                                # Reload the file before deleting
                                df_latest = pd.read_excel(file_path)
                                df_latest.columns = [str(col).strip() for col in df_latest.columns]

                                # Delete the selected Email record using its unique No
                                latest_rename_columns = {}
                                for col in df_latest.columns:
                                    if str(col).strip().lower() in ["no", "email no", "email id", "unique id"]:
                                        latest_rename_columns[col] = "No"

                                df_latest = df_latest.rename(columns=latest_rename_columns)
                                matching_rows = df_latest["No"].fillna("").astype(str).str.strip().str.casefold() == selected_email_no.casefold()

                                if matching_rows.any():
                                    df_latest = df_latest.loc[~matching_rows].reset_index(drop=True)

                                    # Save the updated Excel file
                                    df_latest.to_excel(file_path, index=False)
                                    load_email_data.clear()
                                    st.session_state["searched_delete_email_no"] = ""
                                    st.success(f"Email record '{selected_email_no}' has been deleted.")
                                    st.rerun()
                                else:
                                    st.warning("This Email record could not be found. Please refresh and try again.")

                            except PermissionError:
                                st.error("Please close the Excel file before deleting a record.")

                            except Exception as e:
                                st.error(f"Unable to delete the Email record: {e}")

                    else:
                        st.warning(f"No Email record found with No '{selected_email_no}'.")

                elif search_delete_submitted:
                    st.warning("Please enter an Email No to search.")

    # Search and Filter Email Records
    elif action == "Search Email Records":
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            search = st.text_input("Search Email Records", placeholder="Enter details here (e.g., NPI Name or reference)")

        with col2:
            tis_options = ["All"] + sorted([value for value in df_email["TIS"].unique() if value])
            tis_filter = st.selectbox("Filter by TIS", tis_options)

        with col3:
            pl_options = ["All"] + sorted([value for value in df_email["PL"].unique() if value])
            pl_filter = st.selectbox("Filter by PL", pl_options)

        with col4:
            status_filter = st.selectbox("Filter by status (Completed / Pending)", ["All", "Pending", "Completed"])

        # Apply Table Filters
        df_records = df_email.copy()

        if tis_filter != "All":
            df_records = df_records[df_records["TIS"] == tis_filter]

        if pl_filter != "All":
            df_records = df_records[df_records["PL"] == pl_filter]

        if status_filter != "All":
            df_records = df_records[df_records["Status"] == status_filter]

        if search.strip():
            search_columns = ["No", "TIS", "PL", "ER", "CO/CR/INR/Email", "NPI Name", "Requestor", "Remarks"]
            search_mask = df_records[search_columns].astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False, regex=False)).any(axis=1)
            df_records = df_records[search_mask]

        display_columns = ["No", "TIS", "PL", "ER", "CO/CR/INR/Email", "NPI Name", "Requestor", "Originated Date", "Completion Date", "Status", "Pending Days", "Remarks"]

        st.caption(f"Showing {len(df_records)} of {len(df_email)} Email records.")
        st.dataframe(df_records[display_columns].sort_values("Originated Date", ascending=False, na_position="last"), use_container_width=True, hide_index=True)

        # Download Email Records
        csv_data = df_records[display_columns].to_csv(index=False).encode("utf-8-sig")
        st.download_button(label="Download Email Records (CSV)", data=csv_data, file_name="Email_Records.csv", mime="text/csv")

except PermissionError:
    st.error("Please close the Excel file before managing Email records.")

except Exception as e:
    st.error(f"Unable to load the Email records: {e}")