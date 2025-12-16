import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

def update_status(task_id, new_status):
    try:
        # In a real app, we should pass the token in headers
        response = requests.put(f"{API_URL}/tasks/{task_id}", json={"status": new_status})
        if response.status_code == 200:
            st.rerun()
        else:
            st.error("Failed to update task status")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

def show(user):
    st.header("My Tasks")
    
    # Fetch tasks from API
    try:
        headers = {}
        if "token" in st.session_state and st.session_state.token:
             headers["Authorization"] = f"Bearer {st.session_state.token}"

        response = requests.get(f"{API_URL}/tasks", headers=headers)
        
        if response.status_code == 200:
            tasks = response.json()
        elif response.status_code == 401:
            st.warning("Session expired. Please login again.")
            st.session_state.token = None
            st.rerun()
            tasks = []
        else:
            st.error("Failed to fetch tasks")
            tasks = []
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        tasks = []
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("Pending")
        for task in tasks:
            if task['status'] == 'pending':
                with st.container(border=True):
                    st.write(f"**{task['title']}**")
                    st.caption(f"Priority: {task['priority']}")
                    if st.button("Start", key=f"start_{task['id']}"):
                        update_status(task['id'], "in_progress")
        
    with col2:
        st.subheader("In Progress")
        for task in tasks:
            if task['status'] == 'in_progress':
                with st.container(border=True):
                    st.write(f"**{task['title']}**")
                    st.caption(f"Priority: {task['priority']}")
                    if st.button("Review", key=f"review_{task['id']}"):
                        update_status(task['id'], "review")
        
    with col3:
        st.subheader("Review")
        for task in tasks:
            if task['status'] == 'review':
                with st.container(border=True):
                    st.write(f"**{task['title']}**")
                    st.caption(f"Priority: {task['priority']}")
                    if st.button("Complete", key=f"complete_{task['id']}"):
                        update_status(task['id'], "completed")
        
    with col4:
        st.subheader("Completed")
        for task in tasks:
            if task['status'] == 'completed':
                with st.container(border=True):
                    st.write(f"**{task['title']}**")
                    st.caption(f"Priority: {task['priority']}")
                    # Optional: Archive or Reopen
