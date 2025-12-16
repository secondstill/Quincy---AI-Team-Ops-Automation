import streamlit as st
# from streamlit_webrtc import webrtc_streamer # Uncomment when ready to implement live streaming
import time

def show():
    st.header("Host Meeting")
    
    tab1, tab2 = st.tabs(["Live Meeting", "Upload Recording"])
    
    with tab1:
        st.subheader("Live Audio Recording")
        st.write("Click start to record the meeting audio.")
        if st.button("Start Recording"):
            st.write("Recording... (Mock)")
            # Implementation of WebRTC or simple audio recorder goes here
            
    with tab2:
        st.subheader("Upload Existing Recording")
        uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3", "m4a"])
        if uploaded_file is not None:
            st.audio(uploaded_file, format='audio/wav')
            if st.button("Process Meeting"):
                st.success("Uploaded successfully! Agent is processing...")
                # Call backend upload API here
