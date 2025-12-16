import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

def show():
    st.header("Meeting History")
    
    # Fetch meetings
    try:
        response = requests.get(f"{API_URL}/meetings")
        if response.status_code == 200:
            meetings = response.json()
        else:
            st.error("Failed to fetch meetings")
            meetings = []
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        meetings = []

    if not meetings:
        st.info("No meetings recorded yet.")
        return

    # Layout: List on left, Details on right
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Meetings")
        selected_meeting_id = None
        
        # Simple list selection
        for meeting in meetings:
            label = f"{meeting['title']} ({meeting['date'].split('T')[0]}) - {meeting['status']}"
            if st.button(label, key=meeting['id'], use_container_width=True):
                st.session_state.selected_meeting_id = meeting['id']
                
    with col2:
        st.subheader("Details")
        
        # Refresh button to check for status updates
        col_refresh, col_reprocess = st.columns(2)
        with col_refresh:
            if st.button("Refresh Details"):
                st.rerun()
        
        if "selected_meeting_id" in st.session_state:
            mid = st.session_state.selected_meeting_id
            with col_reprocess:
                if st.button("Retry AI Processing"):
                    try:
                        requests.post(f"{API_URL}/meetings/{mid}/reprocess")
                        st.success("Queued for reprocessing!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")

        if "selected_meeting_id" in st.session_state:
            mid = st.session_state.selected_meeting_id
            
            try:
                res = requests.get(f"{API_URL}/meetings/{mid}")
                if res.status_code == 200:
                    details = res.json()
                    
                    st.write(f"**Title:** {details['title']}")
                    st.write(f"**Date:** {details['date']}")
                    st.write(f"**Status:** {details['status']}")
                    
                    st.divider()
                    
                    tab1, tab2, tab3 = st.tabs(["Summary", "Tasks", "Transcript"])
                    
                    with tab1:
                        if details['summary']:
                            st.markdown(details['summary'])
                        else:
                            st.info("No summary available.")
                            
                    with tab2:
                        if details.get('tasks'):
                            for t in details['tasks']:
                                st.success(f"**{t['title']}** ({t['status']}) - @{t['assignee']}")
                        else:
                            st.info("No tasks extracted.")

                    with tab3:
                        if details['transcript']:
                            st.text_area("Transcript", details['transcript'], height=400)
                        else:
                            st.info("No transcript available.")
                            
                else:
                    st.error("Failed to load details")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.info("Select a meeting to view details.")
