import streamlit as st
from auth import create_user

st.title("Create Account")

username = st.text_input("Username")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Sign Up"):
    create_user(username, email, password)
    st.success("Account created successfully!")