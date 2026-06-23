import streamlit as st
from auth import create_user

st.title("Create Account")


if "username" in st.session_state:
    st.rerun()

with st.form("signup_form"):
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Sign Up")

if submitted:
    try:
        create_user(username, email, password)
    except Exception:
        st.error("Unable to create account. Please try a different username or email.")
    else:
        st.session_state["signup_success_message"] = "Account created successfully! Please log in."
        st.switch_page("views/login.py")
