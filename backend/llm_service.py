import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral" # Or "llama3", depending on what the user has

class LLMService:
    def __init__(self, model=MODEL_NAME):
        self.model = model

    def _generate(self, prompt: str):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama: {e}")
            return None

    def summarize(self, text: str):
        prompt = f"""
        You are an expert meeting assistant. Please provide a concise summary of the following meeting transcript.
        Focus on key decisions and action items.
        
        Transcript:
        {text}
        
        Summary:
        """
        return self._generate(prompt)

    def extract_tasks(self, text: str, valid_users: list = None):
        user_instruction = ""
        if valid_users:
            users_str = ", ".join([f"{u['username']} ({u['full_name']})" for u in valid_users])
            user_instruction = f"Valid assignees are: {users_str}. Map any mentioned names to the closest matching 'username' from this list. If no match is found or the person is not in the list, use 'Unassigned'."

        prompt = f"""
        You are an expert project manager. Extract actionable tasks from the following meeting transcript.
        Return the result ONLY as a JSON array of objects, where each object has "title", "assignee" (username from valid list or "Unassigned"), and "priority" (High/Medium/Low).
        {user_instruction}
        Do not include any markdown formatting or extra text. Just the JSON array.
        
        Transcript:
        {text}
        
        Tasks (JSON):
        """
        response = self._generate(prompt)
        if response:
            try:
                # Clean up potential markdown code blocks
                cleaned_response = response.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned_response)
            except json.JSONDecodeError:
                print("Failed to parse JSON from LLM response")
                return []
        return []
