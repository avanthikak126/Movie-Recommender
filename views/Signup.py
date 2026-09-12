import streamlit as st
from auth import create_user

st.title("Create Account")


if "username" in st.session_state:
    st.rerun()

# --- Success state: account was just created ---
if st.session_state.get("signup_completed"):
    st.success("✅ Account created successfully! You can now log in.")
    if st.button("Go to Login"):
        del st.session_state["signup_completed"]
        st.switch_page("views/login.py")
    st.stop()

# --- Signup form ---
with st.form("signup_form"):
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button(
        "Sign Up",
        disabled=st.session_state.get("signup_in_progress", False),
    )

if submitted:
    username = username.strip()
    email = email.strip()
    if not username or not email or not password:
        st.error("Please fill in all fields.")
    else:
        st.session_state["signup_in_progress"] = True
        try:
            with st.spinner("Creating your account..."):
                create_user(username, email, password)
        except ValueError as e:
            st.session_state["signup_in_progress"] = False
            st.error(str(e))
        except Exception:
            st.session_state["signup_in_progress"] = False
            st.error("Unable to create account. Please try again.")
        else:
            st.session_state["signup_in_progress"] = False
            st.session_state["signup_completed"] = True
            st.rerun()
