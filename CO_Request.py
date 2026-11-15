import pandas as pd
import streamlit as st
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="CO Request", layout="wide")

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

    /* CO Request Type KPI Cards */
    .co-type-card {padding: 17px; border-radius: 10px; min-height: 135px; margin-bottom: 8px;}
    .co-type-card h3 {font-size: 16px; margin: 0 0 14px 0;}
    .co-type-card .co-count {font-size: 32px; font-weight: 700; line-height: 1.2;}
    .co-type-card .co-caption {font-size: 12px; margin-top: 7px;}
    .drawing-card {background-color: #DCEEFF; color: #155A8A;}
    .board-card {background-color: #D9F5E8; color: #176B4D;}
    .programmed-card {background-color: #FFF0CC; color: #8A5A00;}
    .co-type-card h3,
    .co-type-card .co-count,
    .co-type-card .co-caption {color: inherit !important;}
</style>
""", unsafe_allow_html=True)

# Back to Main Page Button
if st.button("Main Page"):
    st.switch_page("app.py")

# Read CO Excel File
@st.cache_data
def load_co_data():

    df = pd.read_csv("Tracking file for drawing validate 1(Khai Yi) 1.csv", encoding="cp1252")

    # Standardize column headings
    df.columns = [str(col).strip() for col in df.columns]

    # Support alternative column names
    rename_columns = {}

    for col in df.columns:
        key = col.strip().lower()

        if key == "co":
            rename_columns[col] = "CO Number"
        elif key in ["co no", "co number"]:
            rename_columns[col] = "CO Number"
        elif key == "npi":
            rename_columns[col] = "NPI Name"
        elif key in ["number of items", "number of item"]:
            rename_columns[col] = "Number of Items"
        elif key == "completed date":
            rename_columns[col] = "Completion Date"
        elif key in ["remarks", "remarks (if any)"]:
            rename_columns[col] = "Remarks"

    df = df.rename(columns=rename_columns)

    # Remove duplicate column names after renaming
    df = df.loc[:, ~df.columns.duplicated()]

    # Remarks is optional
    if "Remarks" not in df.columns:
        df["Remarks"] = ""

    # Check Required Columns
    required_columns = ["TIS", "CO Number", "NPI Name", "Requestor", "Change Details", "Number of Items", "Received Date", "Completion Date"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing Excel columns: " + ", ".join(missing_columns)
        )

    # Data Preprocessing
    df["Received Date"] = pd.to_datetime(df["Received Date"], errors="coerce")
    df["Completion Date"] = pd.to_datetime(df["Completion Date"], errors="coerce")
    df["Number of Items"] = pd.to_numeric(df["Number of Items"], errors="coerce").fillna(0)

    text_columns = ["TIS", "CO Number", "NPI Name", "Requestor", "Change Details", "Remarks"]

    for col in text_columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Determine Work Status from Completion Date
    df["Status"] = df["Completion Date"].apply(lambda x: "Completed" if pd.notna(x) else "Pending")

    # Calculate Pending Days as the difference between Received Date and Completion Date
    df["Pending Days"] = (df["Completion Date"] - df["Received Date"]).dt.days

    return df

try:
    df_co = load_co_data()
except Exception as e:
    st.error(f"Unable to load the CO Excel file: {e}")
    st.exception(e)
    st.stop()


# Dashboard Title
st.markdown("""
<div class="welcome-banner">
    <div class="welcome-label"> WORK RECORD TRACKING SYSTEM </div>
    <div class="welcome-title"> Change Order (CO) Request Dashboard </div>
    <div class="welcome-description"> Analyse CO workload, item volume, processing time, and pending requests </div>
</div>
""", unsafe_allow_html=True)


# Introduction
st.subheader("Why a CO Request is needed?")

with st.container(border=True):
    st.write("A Change Order (CO) is used to request changes to a product or project. It is used to release the drawing, board, programmed part and also Bill Of Material (BOM) Changes")

st.divider()

# Prepare Available Months
received_months = df_co["Received Date"].dropna().dt.to_period("M")
completed_months = df_co["Completion Date"].dropna().dt.to_period("M")

all_months = pd.concat([received_months, completed_months], ignore_index=True).drop_duplicates().sort_values(ascending=False)
month_options = all_months.dt.strftime("%b-%Y").tolist()

if len(month_options) == 0:
    st.warning("No valid CO dates are available.")
    st.stop()

# Overview (accumulated for the current year)
today = pd.Timestamp.today().normalize()

current_year = today.year
year_start = pd.Timestamp(year=current_year, month=1, day=1)
next_year_start = pd.Timestamp(year=current_year + 1, month=1, day=1)

df_co_year = df_co[(df_co["Received Date"] >= year_start) & (df_co["Received Date"] < next_year_start)].copy()

annual_co_received = len(df_co_year)
annual_items_received = int(df_co_year["Number of Items"].sum())
annual_pending_co = int(df_co_year["Completion Date"].isna().sum())

st.subheader(f"Overview - {current_year}")

annual_col1, annual_col2 = st.columns(2)

with annual_col1:
    with st.container(border=True):
        st.metric(label=f"Accumulated CO Requests Received in {current_year}", value=annual_co_received)

with annual_col2:
    with st.container(border=True):
        st.metric(label=f"Accumulated Released Items (drawing, board and programmed part) in {current_year}", value=annual_items_received)

st.divider()

# Select Month (shown after the Annual Overview)
selected_month_label = st.selectbox("Select Month", month_options)
selected_month = pd.Period(pd.to_datetime(selected_month_label, format="%b-%Y"), freq="M")
selected_month_start = selected_month.start_time
selected_month_end = (selected_month + 1).start_time
previous_month_start = selected_month_start - pd.DateOffset(months=1)

# Records received during the selected month (used for month-based analysis)
df_co_month = df_co[(df_co["Received Date"] >= selected_month_start) & (df_co["Received Date"] < selected_month_end)].copy()

# Monthly Overview KPIs
monthly_co_received = len(df_co_month)
monthly_co_pending = int(df_co_month["Completion Date"].isna().sum())
monthly_items_received = int(df_co_month["Number of Items"].sum())

# Calculate CO Requests Received During Selected Month
co_received_this_month = df_co[(df_co["Received Date"] >= selected_month_start) & (df_co["Received Date"] < selected_month_end)].shape[0]

# Calculate CO Requests Received During Previous Month
co_received_last_month = df_co[(df_co["Received Date"] >= previous_month_start) & (df_co["Received Date"] < selected_month_start)].shape[0]
co_received_change = (co_received_this_month - co_received_last_month)

# Calculate CO Requests Completed During Selected Month
co_completed_this_month = df_co[(df_co["Completion Date"] >= selected_month_start) & (df_co["Completion Date"] < selected_month_end)].shape[0]

# Calculate CO Requests Completed During Previous Month
co_completed_last_month = df_co[(df_co["Completion Date"] >= previous_month_start) & (df_co["Completion Date"] < selected_month_start)].shape[0]
co_completed_change = (co_completed_this_month - co_completed_last_month)

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.metric(label="CO Requests Received", value=int(co_received_this_month), delta=f"{co_received_change:+} Requests")

with col2:
    with st.container(border=True):
        st.metric(label="CO Requests Completed", value=int(co_completed_this_month), delta=f"{co_completed_change:+} Requests")

with col3:
    with st.container(border=True):
        st.metric(label="Current Pending COs", value=monthly_co_pending)
        if st.button("View Pending", use_container_width=True):
            st.switch_page("pages/Pending_Work.py")

with st.container(border=True):
    st.subheader(f"CO Trend in {selected_month.strftime('%b-%Y')}")

    # Get all days in the selected month
    days_in_month = selected_month.days_in_month
    daily_data = pd.DataFrame({"Day": range(1, days_in_month + 1)})

    # Count CO requests received each day
    received_data = df_co[(df_co["Received Date"] >= selected_month_start) & (df_co["Received Date"] < selected_month_end)].copy()
    received_data["Day"] = received_data["Received Date"].dt.day
    received_daily = received_data.groupby("Day").size()

    # Count CO requests completed each day
    completed_data = df_co[(df_co["Completion Date"] >= selected_month_start) & (df_co["Completion Date"] < selected_month_end)].copy()
    completed_data["Day"] = completed_data["Completion Date"].dt.day
    completed_daily = completed_data.groupby("Day").size()

    # Add daily totals to the chart data
    daily_data["CO Received"] = daily_data["Day"].map(received_daily).fillna(0).astype(int)
    daily_data["CO Completed"] = daily_data["Day"].map(completed_daily).fillna(0).astype(int)

    # Convert data for the line chart
    daily_chart_data = daily_data.melt(id_vars=["Day"], value_vars=["CO Received", "CO Completed"], var_name="Work Status", value_name="Number of COs")

    # Create daily CO Received line chart
    fig_trend = px.line(daily_data, x="Day", y="CO Received", markers=False, text="CO Received", color_discrete_sequence=["#142D4E"])
    fig_trend.update_traces(textposition="top center", hovertemplate="Day %{x}<br> CO Received: %{y}<extra></extra>")
    fig_trend.update_layout(xaxis_title="Day of Month", yaxis_title="Number of CO Requests Received", plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False)
    fig_trend.update_xaxes(tickmode="linear", tick0=1, dtick=1, range=[0.5, days_in_month + 0.5])
    fig_trend.update_yaxes(rangemode="tozero", dtick=1)

    st.plotly_chart(fig_trend, use_container_width=True)

# Analysis Section
st.divider()
with st.expander("View Monthly Analysis (CLick to expand)", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border = True):
            requestor_data = df_co_month.copy()
            requestor_data["Requestor"] = requestor_data["Requestor"].replace("", "Unspecified")
            requestor_summary = (requestor_data.groupby("Requestor", as_index=False).agg(Total_Requests=("CO Number", "size")).sort_values("Total_Requests", ascending=False))

            top_requestors = requestor_summary.head(10).sort_values("Total_Requests", ascending=True)

            st.subheader(f"Requestor Analysis in {selected_month_label}")

            fig_requestors = px.bar(top_requestors,x="Total_Requests", y="Requestor", orientation="h", text="Total_Requests", color_discrete_sequence=["#193653"])
            fig_requestors.update_traces(textposition="outside", hovertemplate="<b>%{y}</b><br> CO Requests: %{x}<extra></extra>")
            fig_requestors.update_layout(xaxis_title="Number of CO Requests", yaxis_title="", plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False, margin=dict(l=10, r=25, t=15, b=10))
            fig_requestors.update_xaxes(rangemode="tozero", dtick=1)

            st.caption(f"Top 10 requestors in {selected_month_label}.")
            st.plotly_chart(fig_requestors, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.subheader(f"CO Workload for TIS in {selected_month_label}")

            # Filter records for the selected month
            tis_data = df_co_month.copy()
            tis_data["TIS"] = tis_data["TIS"].replace("", "Unassigned")

            # Summarise CO requests by TIS and status
            tis_summary = (tis_data.groupby(["TIS", "Status"], as_index=False).agg(Total_Requests=("CO Number", "size")))

            # Fixed colour for each TIS
            tis_colours = {"Sok Fuen":"#193653", "Pei Ling":"#248F95", "Elaine":"#65BDB7", "Ai Mei":"#D9B568", "Khai Yi":"#D78370"}

            # Give any new TIS a consistent fallback colour
            default_tis_colour = "#9B8AC4"

            all_tis = sorted(tis_summary["TIS"].unique())

            for tis in all_tis:
                if tis not in tis_colours:
                    tis_colours[tis] = default_tis_colour

            fig_tis = px.pie(tis_summary.groupby("TIS", as_index=False)["Total_Requests"].sum(), names="TIS", values="Total_Requests", color="TIS", color_discrete_map=tis_colours)
            fig_tis.update_traces(textinfo="label+percent", textposition="inside", 
                                hovertemplate=("<b>TIS: %{label}</b>"
                                                "<br>CO Requests: %{value}"
                                                "<br>Percentage: %{percent}"
                                                "<extra></extra>"),)

            fig_tis.update_layout(plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False)

            st.caption("The Distributin of Workload for TIS")
            st.plotly_chart(fig_tis, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.subheader(f"Top 5 Busiest NPI in {selected_month_label}")

            # Count CO requests for each NPI Name
            npi_data = df_co_month.copy()

            # Clean NPI Name values
            npi_data["NPI Name"] = (npi_data["NPI Name"].fillna("").astype(str).str.strip())

            # Exclude blank NPI names
            npi_data = npi_data[npi_data["NPI Name"] != ""]

            # Calculate total CO requests for each NPI
            npi_summary = (npi_data.groupby("NPI Name").size().reset_index(name="Total Requests").sort_values("Total Requests", ascending=False).head(10).sort_values("Total Requests", ascending=True))

            fig_npi = px.bar(npi_summary, x="Total Requests", y="NPI Name", orientation="h", text="Total Requests", color_discrete_sequence=["#248F95"],)
            fig_npi.update_traces(textposition="outside", 
                                hovertemplate=("<b>%{y}</b><br>"
                                               "CO Requests: %{x}"
                                               "<extra></extra>"))
            fig_npi.update_layout(xaxis_title="Number of CO Requests", yaxis_title="",  plot_bgcolor="white", paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False, margin=dict(l=10, r=30, t=20, b=10),)
            fig_npi.update_xaxes(rangemode="tozero", dtick=1,)

            st.plotly_chart(fig_npi, use_container_width=True)

    with col4:
        with st.container(border=True):
            st.subheader("Requests by Change Type")

            change_data = df_co_month.copy()
            change_data["Change Details"] = change_data["Change Details"].replace("", "Unspecified")
            change_summary = change_data.groupby("Change Details", as_index=False).agg(Total_Requests=("CO Number", "size"),Total_Items=("Number of Items", "sum"))

            fig_change_requests = px.pie(change_summary, names="Change Details", values="Total_Requests", color_discrete_sequence=["#193653", "#248F95", "#65BDB7", "#D9B568", "#D78370"], hole=0.35)
            fig_change_requests.update_traces( textinfo="label+percent", textposition="inside", hovertemplate=("<b>%{label}</b><br>"
                                                                                                            "Requests: %{value}<br>"
                                                                                                            "Percentage: %{percent}"
                                                                                                            "<extra></extra>"))
            fig_change_requests.update_layout(paper_bgcolor="#F7F9FC", font=dict(color="#142D4E"), showlegend=False)

            st.plotly_chart(fig_change_requests, use_container_width=True)

# CO Record Management (Subsystem)
st.divider()
st.subheader("CO Record Management")

file_path = "Tracking file for drawing validate 1(Khai Yi) 1.csv"
action = st.radio("Select Action", ["Add New Record", "Update Existing Record", "Delete CO Record", "Search CO Records"], horizontal=True, key="co_management_action")

try:
    df_existing = pd.read_csv(file_path, encoding="cp1252")

    # Match the actual column names in your Excel file
    df_existing.columns = [str(col).strip() for col in df_existing.columns]

    co_col = "CO" if "CO" in df_existing.columns else "CO Number"

    completed_col = ("Completed Date"
                     if "Completed Date" in df_existing.columns
                     else "Completion Date")

    items_col = next(
        (col for col in df_existing.columns
         if str(col).strip().casefold() in ["number of items", "number of item"]),
        None
    )

    if items_col is None:
        raise ValueError("Number of Items column not found in Excel file.")

    remarks_col = ("Remarks"
                   if "Remarks" in df_existing.columns
                   else "Remarks (if any)")

    # Add New CO Record
    if action == "Add New Record":
            with st.form("add_co_record_form", clear_on_submit=True):

                col1, col2 = st.columns(2)
                with col1:
                    tis = st.text_input("TIS (Assigned by?)")
                    co_number = st.text_input("CO Number (e.g, CO0123456)")
                    npi_name = st.text_input("NPI Name")
                    requestor = st.text_input("Requestor")

                with col2:
                    change_details = st.selectbox("Change Details", ["Drawing Release", "Board Release", "Programmed Part Release"])
                    number_of_items = st.number_input("Number of Items", min_value=1, step=1)

                    received_date = st.date_input("Received Date (e.g, 14-Oct-26)")
                    remarks = st.text_area("Remarks (Optional)")
                    has_completion_date = st.checkbox("CO already completed")

                    if has_completion_date:
                        completion_date = st.date_input("Completion Date")
                    else:
                        completion_date = None

                submitted = st.form_submit_button("Save CO Record", use_container_width=True)

                if submitted:
                    if not all([tis.strip(), co_number.strip(), npi_name.strip(), requestor.strip()]):
                        st.error("Please fill in TIS, CO Number, NPI Name and Requestor")
                    else:
                        try:
                            # Read the existing CSV file
                            df_existing = pd.read_csv(file_path, encoding="cp1252")
                            df_existing.columns = [str(col).strip() 
                                                   for col in df_existing.columns]
                            co_col = ("CO"
                                      if "CO" in df_existing.columns
                                      else "CO Number")

                            completed_col = ("Completed Date"
                                             if "Completed Date" in df_existing.columns
                                             else "Completion Date")

                            items_col = next(
                                (col for col in df_existing.columns
                                 if str(col).strip().casefold() in ["number of items", "number of item"]),
                                None
                            )

                            if items_col is None:
                                raise ValueError("Number of Items column not found in Excel file.")

                            remarks_col = ("Remarks"
                                           if "Remarks" in df_existing.columns
                                           else "Remarks (if any)")

                            # Check for duplicate CO numbers
                            existing_numbers = (df_existing[co_col].dropna().astype(str).str.strip().str.casefold())

                            if co_number.strip().casefold() in existing_numbers.values:
                                st.error(f"CO Number '{co_number}' already exists")
                                st.stop()

                            # Prepare the new record
                            new_record = {
                                "TIS": tis.strip(),
                                co_col: co_number.strip(),
                                "NPI Name": npi_name.strip(),
                                "Requestor": requestor.strip(),
                                "Change Details": change_details,
                                items_col: number_of_items,
                                "Received Date": pd.to_datetime(received_date),
                                completed_col: (pd.to_datetime(completion_date)
                                                if completion_date is not None
                                                else pd.NaT),
                                remarks_col: remarks.strip()
                            }

                            # Add the new record without replacing existing records
                            df_updated = pd.concat([df_existing, pd.DataFrame([new_record])], ignore_index=True)

                            # Save the updated CSV file
                            df_updated.to_csv(file_path, index=False, encoding="cp1252")
                            load_co_data.clear()
                            st.success(f"CO Record '{co_number}' added successfully!")
                            st.rerun()

                        except PermissionError:
                            st.error("Cannot save the CSV file. Please close it and try again.")

                        except Exception as e:
                            st.error(f"Unable to save the CO record: {e}")

    # Update Existing CO Record
    elif action == "Update Existing Record":
            if df_existing.empty:
                st.info("There are no CO records available to update.")

            else:
                co_numbers = (df_existing[co_col].dropna().astype(str).unique().tolist())
                if not co_numbers:
                    st.info("There are no CO records available to update")
                else:
                    selected_co = st.text_input("Enter CO Number to update", placeholder="Type CO Number (e.g., CO0123456)", key="update_co_number").strip()

                    if selected_co:
                        selected_rows = df_existing[df_existing[co_col].astype(str).str.strip().str.casefold() == selected_co.casefold()]
                    else:
                        selected_rows = df_existing.iloc[0:0]

                    if not selected_rows.empty:
                        record = selected_rows.iloc[0]

                        # Get existing values
                        current_tis = (str(record["TIS"])
                                       if pd.notna(record.get("TIS"))
                                       else "")

                        current_npi = (str(record["NPI Name"])
                                       if pd.notna(record.get("NPI Name"))
                                       else "")

                        current_requestor = (str(record["Requestor"])
                                                 if pd.notna(record.get("Requestor"))
                                                 else "")

                        current_change = (str(record["Change Details"])
                                          if pd.notna(record.get("Change Details"))
                                          else "Drawing Release")

                        change_options = ["Drawing Release", "Board Release", "Programmed Part Release"]

                        if current_change not in change_options:
                            change_options.append(current_change)

                        current_items = (int(record[items_col])
                                         if pd.notna(record.get(items_col)) and int(record[items_col]) >= 1
                                         else 1)

                        current_received_date = (pd.to_datetime(record["Received Date"]).date()
                                                 if pd.notna(record.get("Received Date"))
                                                 else pd.Timestamp.today().date())

                        current_completion_date = (pd.to_datetime(record[completed_col]).date()
                                                   if pd.notna(record.get(completed_col))
                                                   else None)

                        current_remarks = (str(record[remarks_col])
                                           if pd.notna(record.get(remarks_col))
                                           else "")

                        with st.form("update_co_record_form"):
                            st.caption( f"Updating CO Record: {selected_co}")

                            col1, col2 = st.columns(2)
                            with col1:
                                tis = st.text_input("TIS (Assigned by?)", value=current_tis)
                                st.text_input("CO Number", value=selected_co, disabled=True)
                                npi_name = st.text_input("NPI Name", value=current_npi)
                                requestor = st.text_input("Requestor", value=current_requestor)

                            with col2:
                                change_details = st.selectbox("Change Details", change_options, index=change_options.index(current_change))
                                number_of_items = st.number_input("Number of Items", min_value=1, step=1, value=current_items)
                                received_date = st.date_input("Received Date", value=current_received_date)
                                has_completion_date = st.checkbox("CO completed", value=current_completion_date is not None)

                                if has_completion_date:
                                    completion_date = st.date_input("Completion Date",
                                        value=(current_completion_date
                                               if current_completion_date is not None
                                               else pd.Timestamp.today().date())
                                    )
                                else:
                                    completion_date = None

                            remarks = st.text_area("Remarks (Optional)", value=current_remarks)
                            submitted = st.form_submit_button("Update CO Record", use_container_width=True)

                            if submitted:
                                if not all([tis.strip(), npi_name.strip(), requestor.strip()]):
                                    st.error("Please fill in TIS, NPI Name and Requestor")
                                else:
                                    try:
                                        # Reload the file before updating
                                        df_latest = pd.read_csv(file_path, encoding="cp1252")
                                        df_latest.columns = [str(col).strip()
                                                             for col in df_latest.columns]

                                        latest_co_col = ("CO"
                                                         if "CO" in df_latest.columns
                                                         else "CO Number")

                                        latest_matching_rows = (df_latest[latest_co_col].astype(str) == selected_co)

                                        if latest_matching_rows.any():
                                            row_index = df_latest.index[latest_matching_rows][0]

                                            df_latest.loc[row_index, "TIS"] = tis.strip()
                                            df_latest.loc[row_index, "NPI Name"] = npi_name.strip()
                                            df_latest.loc[row_index, "Requestor"] = requestor.strip()
                                            df_latest.loc[row_index, "Change Details"] = change_details

                                            latest_items_col = next(
                                                (col for col in df_latest.columns
                                                 if str(col).strip().casefold() in ["number of items", "number of item"]),
                                                None
                                            )

                                            if latest_items_col is None:
                                                raise ValueError("Number of Items column not found in Excel file.")

                                            latest_completed_col = ("Completed Date"
                                                                    if "Completed Date" in df_latest.columns
                                                                    else "Completion Date")

                                            latest_remarks_col = ("Remarks"
                                                                  if "Remarks" in df_latest.columns
                                                                  else "Remarks (if any)")

                                            df_latest.loc[row_index, latest_items_col] = number_of_items
                                            df_latest.loc[row_index, "Received Date"] = received_date.strftime("%Y-%m-%d")
                                            df_latest.loc[row_index, latest_completed_col] = (completion_date.strftime("%Y-%m-%d")
                                                                                              if completion_date is not None
                                                                                              else pd.NaT)
                                            df_latest.loc[row_index, latest_remarks_col] = remarks.strip()

                                            # Save the updated CSV file
                                            df_latest.to_csv(file_path, index=False, encoding="cp1252")
                                            load_co_data.clear()
                                            st.success(f"CO Record '{selected_co}' updated successfully!")
                                            st.rerun()

                                        else:
                                            st.warning("This CO record could not be found. Please refresh and try again.")

                                    except PermissionError:
                                        st.error("Cannot save the CSV file. Please close it and try again.")

                                    except Exception as e:
                                        st.error(f"Unable to update the CO record: {e}")

    # Delete CO Record
    elif action == "Delete CO Record":
            if df_existing.empty:
                st.info("There are no CO records to delete")

            else:
                co_numbers = ( df_existing[co_col].dropna().astype(str).unique().tolist())

                if not co_numbers:
                    st.info("There are no CO records to delete.")

                else:
                    selected_co = st.text_input("Enter CO Number to delete", placeholder="Type CO Number (e.g., CO0123456)", key="delete_co_number").strip()

                    if selected_co:
                        selected_record = df_existing[df_existing[co_col].astype(str).str.strip().str.casefold() == selected_co.casefold()]
                    else:
                        selected_record = df_existing.iloc[0:0]

                    if not selected_record.empty:
                        record = selected_record.iloc[0]

                        st.write("**Please check this record before deleting:**")
                        st.write(f"**CO Number:** {selected_co}")
                        st.write(f"**NPI Name:** {record.get('NPI Name', '')}")
                        st.write(f"**Requestor:** {record.get('Requestor', '')}")
                        st.write(f"**Change Details:** {record.get('Change Details', '')}")

                        confirm_delete = st.checkbox("Confirm Delete this CO record", key="confirm_delete_co")

                        if st.button("Delete CO Record", type="primary", disabled=not confirm_delete, key="delete_co_button"):
                            try:
                                # Reload the file before deleting
                                df_latest = pd.read_csv(file_path, encoding="cp1252")
                                df_latest.columns = [str(col).strip()
                                                     for col in df_latest.columns]

                                latest_co_col = ("CO"
                                                 if "CO" in df_latest.columns
                                                 else "CO Number")

                                # Delete the selected CO record
                                matching_rows = (df_latest[latest_co_col].astype(str) == selected_co)

                                if matching_rows.any():
                                    df_latest = df_latest.loc[~matching_rows]

                                    # Save the updated CSV file
                                    df_latest.to_csv(file_path, index=False, encoding="cp1252")
                                    load_co_data.clear()
                                    st.success(f"CO record '{selected_co}' has been deleted")
                                    st.rerun()

                                else:
                                    st.warning("This CO record could not be found. Please refresh and try again")

                            except PermissionError:
                                st.error("Please close the CSV file before deleting a record")

                            except Exception as e:
                                st.error(f"Unable to delete the CO record: {e}")

        # Search and Filter CO Records
    elif action == "Search CO Records":
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            search = st.text_input("Search CO Records", placeholder="Enter details here (e.g., CO0123456)")

        with col2:
            tis_filter = st.selectbox("Filter by TIS", ["All", "Ai Mei", "Elaine", "Pei Ling", "Sok Fuen", "Khai Yi"])

        with col3:
            change_options = ["All"] + sorted([value for value in df_co["Change Details"].unique()
                                               if value])

            change_filter = st.selectbox("Filter by Change Details", change_options)

        with col4:
            status_filter = st.selectbox("Filter by status (Completed / Pending)", ["All", "Pending", "Completed"])

        # Apply Table Filters
        df_records = df_co.copy()

        if tis_filter != "All":
            df_records = df_records[df_records["TIS"] == tis_filter]

        if change_filter != "All":
            df_records = df_records[df_records["Change Details"] == change_filter]

        if status_filter != "All":
            df_records = df_records[df_records["Status"] == status_filter]

        if search.strip():
            search_columns = ["TIS", "CO Number", "NPI Name", "Requestor", "Change Details", "Remarks"]
            search_mask = df_records[search_columns].astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False, regex=False)).any(axis=1)
            df_records = df_records[search_mask]

        display_columns = ["TIS", "CO Number", "NPI Name", "Requestor", "Change Details", "Number of Items", "Received Date", "Completion Date", "Status", "Pending Days", "Remarks"]

        st.caption(f"Showing {len(df_records)} of {len(df_co)} CO records.")
        st.dataframe(df_records[display_columns].sort_values("Received Date", ascending=False, na_position="last"), use_container_width=True, hide_index=True)

        # Download CO Records
        csv_data = df_records[display_columns].to_csv(index=False).encode("utf-8-sig")
        st.download_button(label="Download CO Records (CSV)", data=csv_data, file_name="CO_Records.csv", mime="text/csv")

except PermissionError:
    st.error("Please close the CSV file before managing CO records.")

except Exception as e:
    st.error(f"Unable to load the CO records: {e}")