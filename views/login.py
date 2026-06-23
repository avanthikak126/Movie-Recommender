import streamlit as st
from auth import login_user

st.title("Login")


if "username" in st.session_state:
    st.rerun()

if "signup_success_message" in st.session_state:
    st.success(st.session_state.pop("signup_success_message"))

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    user = login_user(username, password)

    if user:
        st.session_state["username"] = username
        st.session_state["logged_in"] = True
        st.rerun()

    else:
        st.error("Invalid username or password")
