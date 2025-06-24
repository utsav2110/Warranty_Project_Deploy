import streamlit as st
from app import login_user

st.title("Login")

username = st.text_input("Username / Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    valid, role, error = login_user(username, password)
    if valid:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state["role"] = role
        st.success(f"Welcome, {username} ({role})")
        st.page_link("app.py", label="Go to Home")
    else:
        st.error(error)  