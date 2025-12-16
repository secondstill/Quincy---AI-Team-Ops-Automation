import sys
import os
import wave
import struct
import math
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.transcription import TranscriptionService

def create_dummy_wav(filename, duration=2.0):
    """Creates a dummy WAV file with a simple tone."""
    sample_rate = 16000
    num_samples = int(duration * sample_rate)
    frequency = 440.0
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
            
    print(f"Created dummy audio file: {filename}")

def test_transcription():
    audio_file = "test_audio.wav"
    try:
        create_dummy_wav(audio_file)
        
        print("Initializing TranscriptionService...")
        # Use small model to verify the upgrade
        service = TranscriptionService(model_size="small", device="cpu", compute_type="int8")
        
        print("Transcribing...")
        text = service.transcribe(audio_file)
        
        print(f"Transcription Result: '{text}'")
        
        if text is not None:
            print("SUCCESS: Transcription service ran and returned a result.")
        else:
            print("FAILURE: Transcription service returned None.")
            
    except Exception as e:
        print(f"FAILURE: An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print("Cleaned up test file.")

if __name__ == "__main__":
    test_transcription()
