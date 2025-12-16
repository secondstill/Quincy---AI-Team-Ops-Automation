import os
from faster_whisper import WhisperModel
import ollama
import json

class AIEngine:
    def __init__(self):
        # Initialize Whisper (small model for speed on CPU/Laptop)
        self.whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
        self.llm_model = "mistral" # Assumes 'mistral' is pulled in Ollama

    def transcribe(self, audio_path: str) -> str:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        segments, info = self.whisper_model.transcribe(audio_path, beam_size=5)
        transcript = " ".join([segment.text for segment in segments])
        return transcript

    def summarize(self, text: str) -> str:
        prompt = f"""
        You are an expert meeting secretary. Summarize the following meeting transcript.
        Include Key Discussion Points, Decisions Made, and Action Items.
        
        Transcript:
        {text}
        """
        response = ollama.chat(model=self.llm_model, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']

    def extract_tasks(self, text: str) -> list:
        prompt = f"""
        Extract all action items from this meeting transcript.
        Return ONLY a JSON array of objects with keys: "title", "assigned_to", "priority" (High/Medium/Low), "due_date" (YYYY-MM-DD or null).
        If no assignee is mentioned, use "Unassigned".
        
        Transcript:
        {text}
        """
        response = ollama.chat(model=self.llm_model, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        
        # Basic cleanup to ensure JSON
        try:
            # Find the first [ and last ]
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return []
        except:
            return []

# Singleton instance
ai_engine = AIEngine()
