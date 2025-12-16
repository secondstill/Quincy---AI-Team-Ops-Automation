import requests
import sys
import os

# Setup paths
sys.path.append(os.getcwd())
from backend.database import SessionLocal, Meeting, Summary, Task, Transcript

def check_ollama():
    print("\n--- Checking Ollama ---")
    try:
        # Check if running
        resp = requests.get("http://localhost:11434")
        if resp.status_code == 200:
            print("✅ Ollama is running.")
        else:
            print("❌ Ollama returned unexpected status:", resp.status_code)
            return False

        # Check for mistral model
        resp = requests.get("http://localhost:11434/api/tags")
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json()['models']]
            print(f"Available models: {models}")
            if "mistral:latest" in models or "mistral" in models:
                print("✅ 'mistral' model found.")
            else:
                print("❌ 'mistral' model NOT found. Please run 'ollama pull mistral'")
        else:
            print("❌ Failed to fetch models.")
            
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        print("👉 Make sure Ollama is installed and running!")
        return False
    return True

def check_db():
    print("\n--- Checking Database ---")
    try:
        db = SessionLocal()
        meetings = db.query(Meeting).all()
        print(f"Total Meetings: {len(meetings)}")
        for m in meetings:
            t_count = db.query(Transcript).filter(Transcript.meeting_id == m.id).count()
            summary = db.query(Summary).filter(Summary.meeting_id == m.id).first()
            s_len = len(summary.content) if summary and summary.content else 0
            task_count = db.query(Task).filter(Task.meeting_id == m.id).count()
            print(f"  - Meeting '{m.title}' (Status: {m.status})")
            print(f"    - Transcript: {'✅' if t_count else '❌'}")
            print(f"    - Summary:    {'✅' if s_len > 0 else '❌'} (Len: {s_len})")
            print(f"    - Tasks:      {task_count}")
        db.close()
    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    check_ollama()
    check_db()
