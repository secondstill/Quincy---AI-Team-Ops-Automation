import streamlit as st
from dashboard import show as show_dashboard
# Will import meeting_room after creating it
# from meeting_room import show as show_meeting_room

st.set_page_config(page_title="Quincy", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def main():
    st.sidebar.title("Quincy")
    
    # Login Logic
    if not st.session_state.token:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                import requests
                # The backend expects form data for OAuth2
                response = requests.post(
                    "http://127.0.0.1:8000/token", 
                    json={"username": username, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user = {
                        "username": username, 
                        "role": data["role"], 
                        "id": data["user_id"],
                        "full_name": data["full_name"]
                    }
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            except Exception as e:
                st.error(f"Login failed: {e}")
        return

    st.sidebar.write(f"Welcome, {st.session_state.user['username']}")
    
    options = ["Dashboard", "Meeting Room", "Calendar", "History"]
    if st.session_state.user['role'] == 'admin':
        options.append("Admin Panel")
        
    page = st.sidebar.radio("Navigate", options)
    
    if page == "Dashboard":
        show_dashboard(st.session_state.user)
    elif page == "Meeting Room":
        import meeting_room
        meeting_room.show()
    elif page == "Calendar":
        import calendar_view
        calendar_view.show()
    elif page == "History":
        import history
        history.show()
    elif page == "Admin Panel":
        import admin_panel
        admin_panel.show()
        
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()

if __name__ == "__main__":
    main()
