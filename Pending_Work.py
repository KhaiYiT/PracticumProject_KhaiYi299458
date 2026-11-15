import pandas as pd
import streamlit as st
from datetime import date
from openpyxl import load_workbook

# Page Configuration
st.set_page_config(page_title="Pending Work", layout="wide")

EMAIL_FILE = "Request Tracking File(Santa Rosa - 2026).xlsx"
CO_FILE = "Tracking file for drawing validate 1(Khai Yi) 1.csv"

# Page Styling
st.markdown("""
<style>
    .stApp { background-color: #F7F9FC; color: #142D4E;}
    .main .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}

    h1, h2, h3 {color: #142D4E !important;}
    p {color: #334B63;}

    section[data-testid="stSidebar"] {display: none;}
    button[data-testid="stSidebarCollapseButton"] {display: none;}

    [data-testid="stHeader"] {display: none;}

    .welcome-banner {background-color: #142D4E; padding: 22px 24px; border-radius: 10px; margin-top: 15px; margin-bottom: 22px;}
    .welcome-label {color: #80DED5 !important; font-size: 13px; font-weight: 700; margin-bottom: 10px;}
    .welcome-title {color: #FFFFFF !important; font-size: 27px; font-weight: 700; margin-bottom: 10px;}
    .welcome-description {color: #E5EDF6 !important; font-size: 15px; margin-bottom: 0;}

    div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #FFFFFF; border: 1px solid #D5E0ED; border-radius: 10px; padding: 8px;}
    div.stButton > button {background-color: #142D4E; color: #FFFFFF !important; border: 1px solid #142D4E; border-radius: 7px; padding: 0.55rem 1rem; font-weight: 600;}
    div.stButton > button p {color: #FFFFFF !important;}
    div.stButton > button:hover {background-color: #19A7A1; color: #FFFFFF !important; border-color: #19A7A1;}
    div.stButton > button:hover p {color: #FFFFFF !important;}

    hr {border-color: #D5E0ED;}
</style>
""", unsafe_allow_html=True)

def find_column(df, possible_names):
    columns = {
        str(col).strip().casefold(): col
        for col in df.columns
    }

    for name in possible_names:
        if name.casefold() in columns:
            return columns[name.casefold()]
        
    return None


def load_pending(file_path):
    if file_path.lower().endswith(".csv"):
        df = pd.read_csv(file_path, encoding="cp1252")
    else:
        df = pd.read_excel(file_path, engine="openpyxl")

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    completion_col = find_column(
        df, ["Completion Date", "Completed Date"]
    )

    if completion_col is None:
        raise ValueError("Completion Date column not found.")

    pending = df[
        df[completion_col].isna()
        | (df[completion_col].astype(str).str.strip() == "")
    ].copy()

    return pending, completion_col


def update_record(file_path, row_index, action):

    # Handle CSV file (CO Request)
    if file_path.lower().endswith(".csv"):

        df = pd.read_csv(file_path, encoding="cp1252")

        df.columns = [
            str(col).strip()
            for col in df.columns
        ]

        if action == "complete":

            completion_col = find_column(
                df, ["Completion Date", "Completed Date"]
            )

            if completion_col is None:
                raise ValueError("Completion Date column not found.")

            df.loc[row_index, completion_col] = date.today().strftime("%Y-%m-%d")

        elif action == "delete":

            df = df.drop(index=row_index)

        df.to_csv(
            file_path,
            index=False,
            encoding="cp1252"
        )

    # Handle Excel file (Email Request)
    else:

        workbook = load_workbook(file_path)
        sheet = workbook.active

        if action == "complete":

            completion_col = None

            for cell in sheet[1]:
                if str(cell.value).strip().casefold() in [
                    "completion date",
                    "completed date"
                ]:
                    completion_col = cell.column
                    break

            if completion_col is None:
                workbook.close()
                raise ValueError("Completion Date column not found.")

            sheet.cell(
                row=row_index + 2,
                column=completion_col
            ).value = date.today()

        elif action == "delete":

            sheet.delete_rows(row_index + 2, 1)

        workbook.save(file_path)
        workbook.close()

# Navigation and Header
if st.button("Main Page"):
    st.switch_page("app.py")

st.markdown("""
<div class="welcome-banner">
    <div class="welcome-label"> WORK RECORD TRACKING SYSTEM </div>
    <div class="welcome-title"> Pending Work </div>
    <div class="welcome-description"> View and manage outstanding Email and CO requests </div>
</div>
""", unsafe_allow_html=True)

# Email Pending Work
st.subheader("Email Pending Work")

try:
    email_pending, email_completion_col = load_pending(EMAIL_FILE)
    email_no_col = find_column(email_pending, ["No", "Email No", "Email ID", "Unique ID"])

    if email_no_col is None:
        raise ValueError("Email No column not found.")

    if email_pending.empty:
        st.info("There are no pending Email requests.")

    else:
        st.dataframe(email_pending, use_container_width=True, hide_index=True)

        with st.form("search_email_pending_form"):
            email_search_no = st.text_input("Search Email Request by No", placeholder="Enter Email No (e.g., NPI12345678)")
            email_search_submitted = st.form_submit_button("Search", use_container_width=True)

        if email_search_submitted:
            st.session_state["email_pending_search_no"] = email_search_no.strip()
            st.session_state["email_pending_selected"] = None

            if email_search_no.strip():
                email_matching_rows = email_pending[email_pending[email_no_col].astype(str).str.strip().str.casefold() == email_search_no.strip().casefold()]

                if not email_matching_rows.empty:
                    st.session_state["email_pending_selected"] = int(email_matching_rows.index[0])
                else:
                    st.warning(f"No pending Email request found with No '{email_search_no}'.")

            else:
                st.warning("Please enter an Email No to search.")

        email_selected = st.session_state.get("email_pending_selected")

        if email_selected is not None:
            if email_selected in email_pending.index:
                selected_email_record = email_pending.loc[[email_selected]]

                st.success(f"Email request '{selected_email_record.iloc[0][email_no_col]}' found.")
                st.dataframe(selected_email_record, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Mark as Complete", key="email_complete", use_container_width=True):
                        update_record(EMAIL_FILE, email_selected, "complete")

                        st.session_state["email_pending_selected"] = None
                        st.success("Email request marked as complete.")
                        st.rerun()

                with col2:
                    if st.button("Delete Record", key="email_delete", use_container_width=True):
                        update_record(EMAIL_FILE, email_selected, "delete")

                        st.session_state["email_pending_selected"] = None
                        st.success("Email request deleted successfully.")
                        st.rerun()
            else:
                st.session_state["email_pending_selected"] = None


except FileNotFoundError:
    st.error(f"Cannot find {EMAIL_FILE}.")

except Exception as e:
    st.error(f"Unable to load Email records: {e}")


# CO Pending Work
st.divider()
st.subheader("CO Pending Work")

try:
    co_pending, co_completion_col = load_pending(CO_FILE)
    co_number_col = find_column(co_pending, ["CO", "CO Number"])

    if co_number_col is None:
        raise ValueError("CO Number column not found.")

    if co_pending.empty:
        st.info("There are no pending CO requests.")
    else:
        st.dataframe(co_pending, use_container_width=True, hide_index=True)

        with st.form("search_co_pending_form"):
            co_search_no = st.text_input("Search CO Request by CO Number", placeholder="Enter CO Number (e.g., CO123456)")
            co_search_submitted = st.form_submit_button("Search", use_container_width=True)

        if co_search_submitted:
            st.session_state["co_pending_search_no"] = co_search_no.strip()
            st.session_state["co_pending_selected"] = None

            if co_search_no.strip():
                co_matching_rows = co_pending[co_pending[co_number_col].astype(str).str.strip().str.casefold() == co_search_no.strip().casefold()]

                if not co_matching_rows.empty:
                    st.session_state["co_pending_selected"] = int(co_matching_rows.index[0])
                else:
                    st.warning(f"No pending CO request found with CO Number '{co_search_no}'.")

            else:
                st.warning("Please enter a CO Number to search.")

        co_selected = st.session_state.get("co_pending_selected")

        if co_selected is not None:

            if co_selected in co_pending.index:
                selected_co_record = co_pending.loc[[co_selected]]

                st.success(f"CO request '{selected_co_record.iloc[0][co_number_col]}' found.")
                st.dataframe(selected_co_record, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Mark as Complete", key="co_complete", use_container_width=True):
                        update_record(CO_FILE, co_selected, "complete")

                        st.session_state["co_pending_selected"] = None
                        st.success("CO request marked as complete.")
                        st.rerun()

                with col2:
                    if st.button("Delete Record", key="co_delete", use_container_width=True):
                        update_record(CO_FILE, co_selected, "delete")

                        st.session_state["co_pending_selected"] = None
                        st.success("CO request deleted successfully.")
                        st.rerun()

            else:
                st.session_state["co_pending_selected"] = None


except FileNotFoundError:
    st.error(f"Cannot find {CO_FILE}.")

except Exception as e:
    st.error(f"Unable to load CO records: {e}")