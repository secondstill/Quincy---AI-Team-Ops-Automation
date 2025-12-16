import streamlit as st
from streamlit_calendar import calendar
import requests
import datetime

API_URL = "http://127.0.0.1:8000"

def show():
    st.header("Calendar")
    
    # Fetch Data
    events = []
    
    # 1. Fetch Meetings
    try:
        resp = requests.get(f"{API_URL}/meetings")
        if resp.status_code == 200:
            meetings = resp.json()
            for m in meetings:
                # Parse date
                start_time = m['date'] # ISO format string
                # Create event
                events.append({
                    "title": f"📅 {m['title']}",
                    "start": start_time,
                    "end": start_time, # For now same as start, or add 1 hour
                    "backgroundColor": "#3b82f6", # Blue
                    "borderColor": "#3b82f6"
                })
    except Exception as e:
        st.error(f"Error fetching meetings: {e}")

    # 2. Fetch Tasks
    try:
        # Need token for tasks usually, but simplified for now or check session
        headers = {}
        if "token" in st.session_state and st.session_state.token:
             headers["Authorization"] = f"Bearer {st.session_state.token}"
             
        resp = requests.get(f"{API_URL}/tasks", headers=headers)
        if resp.status_code == 200:
            tasks = resp.json()
            for t in tasks:
                if t.get('due_date'):
                    events.append({
                        "title": f"✅ {t['title']}",
                        "start": t['due_date'],
                        "backgroundColor": "#10b981", # Green
                        "borderColor": "#10b981"
                    }) 
    except Exception as e:
        st.error(f"Error fetching tasks: {e}")

    # Calendar Options
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        },
        "initialView": "dayGridMonth",
    }
    
    calendar(events=events, options=calendar_options)
