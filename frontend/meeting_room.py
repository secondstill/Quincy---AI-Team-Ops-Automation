import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import os
import time
import queue
import threading
import requests
import wave
import numpy as np
import collections
import datetime

# Audio settings
CHANNELS = 1
RATE = 16000 
CHUNK = 1024
API_URL = "http://127.0.0.1:8000"

TRANSCRIPT_BUFFER = collections.deque(maxlen=10) 
TRANSCRIPT_LOCK = threading.Lock()

class AudioProcessor:
    def __init__(self, output_file):
        self.output_file = output_file
        self.wave_file = None
        self.sample_rate = None
        self.channels = None
        self.chunk_buffer = []
        self.chunk_duration_ms = 0
        self.target_chunk_ms = 3000 
        
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        if self.wave_file is None:
            self.sample_rate = frame.sample_rate
            self.channels = len(frame.layout.channels)
            self.wave_file = wave.open(self.output_file, "wb")
            self.wave_file.setnchannels(self.channels)
            self.wave_file.setsampwidth(2)
            self.wave_file.setframerate(self.sample_rate)

        chunk = frame.to_ndarray()
        if frame.format.name in ['fltp', 'flt']:
            chunk = (chunk * 32767).astype(np.int16)
        elif frame.format.name in ['s16', 's16p']:
            chunk = chunk.astype(np.int16)
        if self.channels > 1 and chunk.ndim == 2 and chunk.shape[0] == self.channels:
            chunk = chunk.T.flatten()
        self.wave_file.writeframes(chunk.tobytes())
        
        self.chunk_buffer.append(chunk)
        samples = len(chunk) / self.channels
        duration_ms = (samples / self.sample_rate) * 1000
        self.chunk_duration_ms += duration_ms
        
        if self.chunk_duration_ms >= self.target_chunk_ms:
            self.process_chunk()
        return frame

    def process_chunk(self):
        full_chunk = np.concatenate(self.chunk_buffer)
        self.chunk_buffer = []
        self.chunk_duration_ms = 0
        threading.Thread(target=self._send_chunk, args=(full_chunk, self.sample_rate, self.channels)).start()

    def _send_chunk(self, audio_data, rate, channels):
        try:
            import io
            temp_name = f"temp_rt_{time.time()}.wav"
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(rate)
                wf.writeframes(audio_data.tobytes())
            wav_buffer.seek(0)
            files = {"file": (temp_name, wav_buffer, "audio/wav")}
            response = requests.post(f"{API_URL}/transcribe_chunk", files=files)
            if response.status_code == 200:
                text = response.json().get("text", "")
                if text.strip():
                    with TRANSCRIPT_LOCK:
                        TRANSCRIPT_BUFFER.append(text)
        except Exception as e:
            print(f"RT Error: {e}")

    def close(self):
        if self.wave_file:
            self.wave_file.close()
            self.wave_file = None

def create_audio_processor(output_file):
    return AudioProcessor(output_file)

def show():
    st.header("Meeting Room")
    
    # --- Scheduling Section ---
    with st.expander("📅 Schedule New Meeting"):
        with st.form("schedule_form"):
            new_title = st.text_input("Meeting Title")
            new_date = st.date_input("Date", datetime.date.today())
            new_time = st.time_input("Time", datetime.datetime.now().time())
            if st.form_submit_button("Schedule"):
                dt = datetime.datetime.combine(new_date, new_time)
                try:
                    # Need token for auth usually, but simplified
                    res = requests.post(f"{API_URL}/meetings/schedule", json={"title": new_title, "date": dt.isoformat()})
                    if res.status_code == 200:
                        st.success("Meeting Scheduled!")
                        st.rerun()
                    else:
                        st.error("Failed to schedule")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- Selection Section ---
    st.subheader("Upcoming Meetings")
    try:
        res = requests.get(f"{API_URL}/meetings") # This returns all, we need to filter or update endpoint
        # For now, filter client side
        if res.status_code == 200:
            all_meetings = res.json()
            scheduled = [m for m in all_meetings if m['status'] == 'scheduled']
        else:
            scheduled = []
    except:
        scheduled = []

    selected_meeting = None
    meeting_options = {m['id']: f"{m['title']} ({m['date']})" for m in scheduled}
    meeting_options[0] = "Quick Start (New Meeting)"
    
    selected_id = st.selectbox("Select Meeting to Start", options=meeting_options.keys(), format_func=lambda x: meeting_options[x])
    
    if selected_id != 0:
        # Find the meeting object
        selected_meeting = next((m for m in scheduled if m['id'] == selected_id), None)
        st.info(f"Ready to start: **{selected_meeting['title']}**")
    else:
        st.info("Starting a new ad-hoc meeting.")

    st.divider()

    # --- Recording Section ---
    # Initialize session state for filename
    if "current_meeting_file" not in st.session_state:
        st.session_state.current_meeting_file = f"data/temp_{int(time.time())}.wav"

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Live Feed")
        
        import functools
        ctx = webrtc_streamer(
            key="meeting-room",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTCConfiguration(
                {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
            ),
            media_stream_constraints={"video": True, "audio": True},
            async_processing=True,
            audio_processor_factory=functools.partial(create_audio_processor, st.session_state.current_meeting_file),
        )
        
        st.write("### 🔴 Live Transcript")
        auto_refresh = st.checkbox("Auto-refresh Transcript", value=False)
        transcript_container = st.empty()
        
        if auto_refresh and ctx.state.playing:
            time.sleep(1)
            st.rerun()
            
        with TRANSCRIPT_LOCK:
            full_text = " ".join(TRANSCRIPT_BUFFER)
            if full_text:
                transcript_container.info(f"... {full_text}")
            else:
                transcript_container.caption("Waiting for speech...")

    with col2:
        st.write("### Controls")
        
        # If scheduled, disable title edit
        if selected_meeting:
            meeting_title = st.text_input("Meeting Title", value=selected_meeting['title'], disabled=True)
        else:
            meeting_title = st.text_input("Meeting Title", value="Daily Standup")
        
        if ctx.state.playing:
            st.success("Meeting is Live & Recording...")
        
        if st.button("End & Process Meeting", type="primary"):
            if ctx.audio_processor:
                ctx.audio_processor.close()
            
            temp_path = st.session_state.current_meeting_file
            if os.path.exists(temp_path):
                final_path = f"data/meeting_{int(time.time())}.wav"
                try:
                    import shutil
                    shutil.copy(temp_path, final_path)
                    try: os.remove(temp_path)
                    except: pass
                        
                    st.success(f"Meeting saved to {final_path}")
                    st.info("Processing started...")
                    del st.session_state.current_meeting_file
                    
                    try:
                        payload = {"filename": final_path, "title": meeting_title}
                        if selected_meeting:
                            payload["meeting_id"] = selected_meeting['id']
                            
                        response = requests.post(f"{API_URL}/process_meeting", json=payload)
                        
                        if response.status_code == 200:
                            st.success(f"Processing triggered!")
                        else:
                            st.error(f"Failed: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                        
                except Exception as e:
                    st.error(f"Error saving file: {e}")
            else:
                st.warning("No recording found.")
