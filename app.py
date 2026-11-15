import streamlit as st

# Page Configuration
st.set_page_config(page_title = "Work Record Tracking System", layout = "wide")

# Custom Page Styling
st.markdown("""
    <style>

    /* Main Background */
    .stApp {background-color: #F7F9FC; color: #142D4E;}
    .main .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1050px;}

    /* Main Headings */
    h1, h2, h3 {color: #142D4E !important;}

    /* General Text */
    p {color: #334B63;}

    /* Hide Left Navigation Sidebar */
    section[data-testid="stSidebar"] {display: none;}

    /* Hide Sidebar Collapse Button */
    button[data-testid="stSidebarCollapseButton"] {display: none;}

    /* Welcome Banner */
    .welcome-banner {background-color: #142D4E; padding: 22px 24px; border-radius: 10px; margin-bottom: 22px;}
    .welcome-label {color: #80DED5 !important; font-size: 13px; font-weight: 700; margin-bottom: 10px;}
    .welcome-title {color: #FFFFFF !important; font-size: 27px; font-weight: 700; margin-bottom: 10px;}
    .welcome-description {color: #E5EDF6 !important; font-size: 15px; margin-bottom: 0;}

    /* Navigation Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #FFFFFF; border: 1px solid #D5E0ED; border-radius: 10px; padding: 10px;}

    /* Buttons */
    div.stButton > button {background-color: #142D4E; color: #FFFFFF !important; border: 1px solid #142D4E; border-radius: 7px; padding: 0.55rem 1rem; font-weight: 600; transition: 0.2s;}

    /* Button Text */
    div.stButton > button p {color: #FFFFFF !important;}

    /* Button Hover Effect */
    div.stButton > button:hover {background-color: #19A7A1; color: #FFFFFF !important; border-color: #19A7A1;}
    div.stButton > button:hover p {color: #FFFFFF !important;}

    /* Horizontal Divider */
    hr {border-color: #D5E0ED;}

    </style>
    """, unsafe_allow_html = True)


# Main Page Title <div class="welcome-label"> Work smarter. Track better </div>
st.markdown("""
    <div class="welcome-banner">
        <div class="welcome-title"> WORK RECORD TRACKING SYSTEM </div>
        <div class="welcome-description">
            Manage requests, monitor performance, and keep track of outstanding work.
        </div>
    </div>
    """, unsafe_allow_html = True)

st.divider()

# System Overview
st.subheader("Main Menu")
st.write("Select a page below to explore the relevant information.")

# Dashboard Navigation Cards
col1, col2 = st.columns(2)
with col1:
    with st.container(border = True):
        st.subheader("📊 Overall Dashboard")
        st.write("View overall workload and performance.")
        if st.button("View Overall Dashboard", use_container_width = True):
            st.switch_page("pages/Overall.py")

with col2:
    with st.container(border = True):
        st.subheader("📋 CO Request")
        st.write("Review CO requests and release categories.")
        if st.button("View CO Request", use_container_width = True):
            st.switch_page("pages/CO_Request.py")

col3, col4 = st.columns(2)
with col3:
    with st.container(border = True):
        st.subheader("📧 Email Request")
        st.write("Review Email Requests and their progress.")
        if st.button("View Email Request", use_container_width = True):
            st.switch_page("pages/Email_Request.py")

with col4:
    with st.container(border = True):
        st.subheader("⏳ Pending Work")
        st.write("Review requests that have not yet been completed.")
        if st.button("View Pending Work", use_container_width = True):
            st.switch_page("pages/Pending_Work.py")

st.divider()