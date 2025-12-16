import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

def show():
    st.header("Admin Panel")
    
    st.subheader("Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_fullname = st.text_input("Full Name")
        new_role = st.selectbox("Role", ["employee", "admin"])
        
        if st.form_submit_button("Create User"):
            if new_username and new_password:
                try:
                    # We should probably send the admin token for authorization if the backend required it
                    # But the current /users/ endpoint in main.py is open (no dependency on current_user)
                    # We might want to secure it later, but for now it works.
                    
                    payload = {
                        "username": new_username,
                        "password": new_password,
                        "full_name": new_fullname,
                        "role": new_role
                    }
                    res = requests.post(f"{API_URL}/users/", json=payload)
                    if res.status_code == 200:
                        st.success(f"User '{new_username}' created successfully!")
                    elif res.status_code == 400:
                        st.error("Username already exists.")
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
            else:
                st.warning("Please fill in all fields.")

    st.divider()
    
    st.subheader("Existing Users")
    if st.button("Refresh User List"):
        try:
            res = requests.get(f"{API_URL}/users/")
            if res.status_code == 200:
                users = res.json()
                for u in users:
                    st.text(f"ID: {u['id']} | {u['username']} ({u['role']}) - {u['full_name']}")
            else:
                st.error("Failed to fetch users")
        except Exception as e:
            st.error(f"Error: {e}")
