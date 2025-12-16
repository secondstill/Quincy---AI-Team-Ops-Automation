import time
import logging
import sys
import os

# Ensure we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.database import SessionLocal, Meeting, Transcript, Summary, Task, User
from backend.transcription import TranscriptionService
from backend.llm_service import LLMService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Orchestrator")

def find_user_by_name(db: Session, name: str):
    """
    Simple heuristic to find a user by name.
    Checks username and full_name (case-insensitive).
    """
    if not name or name.lower() == "unassigned":
        return None
    
    # 1. Exact match username
    user = db.query(User).filter(User.username == name).first()
    if user: return user
    
    # 2. Case-insensitive match username
    user = db.query(User).filter(User.username.ilike(name)).first()
    if user: return user

    # 3. Partial match full_name
    user = db.query(User).filter(User.full_name.ilike(f"%{name}%")).first()
    if user: return user
    
    return None

def process_meeting(meeting_id: int):
    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            logger.error(f"Meeting {meeting_id} not found")
            return

        logger.info(f"Starting processing for Meeting {meeting_id} ({meeting.title})")
        
        # 1. Update Status
        meeting.status = "processing"
        db.commit()

        # 2. Transcribe
        logger.info("Step 1/3: Transcribing...")
        ts = TranscriptionService()
        transcript_text = ts.transcribe(meeting.audio_path)
        
        # Save Transcript
        # Check if exists first to avoid duplicates if retrying
        existing_transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting.id).first()
        if not existing_transcript:
            db_transcript = Transcript(meeting_id=meeting.id, text=transcript_text)
            db.add(db_transcript)
        else:
            existing_transcript.text = transcript_text
        db.commit()

        # 3. Summarize & Extract
        logger.info("Step 2/3: Summarizing & Extracting Tasks...")
        ls = LLMService()
        
        # Summary
        summary_text = ls.summarize(transcript_text)
        existing_summary = db.query(Summary).filter(Summary.meeting_id == meeting.id).first()
        if not existing_summary:
            db_summary = Summary(meeting_id=meeting.id, content=summary_text)
            db.add(db_summary)
        else:
            existing_summary.content = summary_text
            
        # Tasks
        tasks_data = ls.extract_tasks(transcript_text)
        
        logger.info(f"Step 3/3: Mapping {len(tasks_data)} tasks to users...")
        for task_item in tasks_data:
            assignee_name = task_item.get("assignee", "Unassigned")
            assigned_user = find_user_by_name(db, assignee_name)
            
            user_id = assigned_user.id if assigned_user else None
            log_msg = f"Task: '{task_item.get('title')}' -> Assignee: '{assignee_name}' -> UserID: {user_id}"
            logger.info(log_msg)

            new_task = Task(
                meeting_id=meeting.id,
                title=task_item.get("title", "Untitled Task"),
                description=f"Extracted from meeting. Priority: {task_item.get('priority', 'Medium')}",
                assigned_to=user_id,
                priority=task_item.get("priority", "Medium"),
                status="pending"
            )
            db.add(new_task)
        
        # 4. Complete
        meeting.status = "completed"
        db.commit()
        logger.info(f"Meeting {meeting_id} processing COMPLETE!")

    except Exception as e:
        logger.error(f"Error processing meeting {meeting_id}: {e}")
        # Re-query meeting to ensure session is valid
        try:
            meeting.status = "failed"
            db.commit()
        except:
            db.rollback()
    finally:
        db.close()

def run_orchestrator_loop():
    """Continuous loop to check for new recordings"""
    logger.info("Orchestrator Watchdog started. Waiting for 'recorded' meetings...")
    while True:
        db = SessionLocal()
        try:
            # Find meetings that are 'recorded' (waiting) or 'queued'
            # We process them one by one
            meetings = db.query(Meeting).filter(Meeting.status.in_(["recorded", "queued"])).all()
            
            if meetings:
                logger.info(f"Found {len(meetings)} pending meetings.")
                for meeting in meetings:
                    process_meeting(meeting.id)
            
        except Exception as e:
            logger.error(f"Orchestrator loop error: {e}")
        finally:
            db.close()
        
        time.sleep(5) # Check every 5 seconds

if __name__ == "__main__":
    run_orchestrator_loop()
