from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import database, auth, transcription, llm_service
from pydantic import BaseModel
from typing import List, Optional
from jose import JWTError, jwt
import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Quincy API")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "employee"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    class Config:
        orm_mode = True

@app.on_event("startup")
def startup():
    database.init_db()

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(database.User).filter(database.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = database.User(username=user.username, hashed_password=hashed_password, full_name=user.full_name, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "role": user.role, "full_name": user.full_name}

@app.get("/users/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(database.User).offset(skip).limit(limit).all()
    return users

@app.post("/upload_audio")
def upload_audio(file: UploadFile = File(...), title: str = Form(...), db: Session = Depends(get_db)):
    # Save file locally
    file_location = f"data/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    
    # Create Meeting entry
    new_meeting = database.Meeting(title=title, audio_path=file_location, status="recorded")
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)
    return {"info": f"file '{file.filename}' saved", "meeting_id": new_meeting.id}

# Helper to decode token for dependency
def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(database.User).filter(database.User.username == username).first()
    if user is None:
        raise credentials_exception
    return Token(access_token=token, token_type="bearer", user_id=user.id, role=user.role, full_name=user.full_name)

@app.get("/tasks", response_model=List[dict]) # Simplified response model for now
def get_tasks(current_user: Token = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    # If admin, show all. If employee, show assigned.
    # Note: Simplified logic. In real app, check role.
    tasks = db.query(database.Task).filter(database.Task.assigned_to == current_user.user_id).all()
    return [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "due_date": t.due_date} for t in tasks]

class TaskUpdate(BaseModel):
    status: str

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(database.Task).filter(database.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = task_update.status
    db.commit()
    return {"message": "Task updated"}

@app.get("/meetings", response_model=List[dict])
def get_meetings(db: Session = Depends(get_db)):
    meetings = db.query(database.Meeting).order_by(database.Meeting.date.desc()).all()
    return [{"id": m.id, "title": m.title, "date": m.date, "status": m.status} for m in meetings]

@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(database.Meeting).filter(database.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    transcript = db.query(database.Transcript).filter(database.Transcript.meeting_id == meeting_id).first()
    summary = db.query(database.Summary).filter(database.Summary.meeting_id == meeting_id).first()
    
    return {
        "id": meeting.id,
        "title": meeting.title,
        "date": meeting.date,
        "status": meeting.status,
        "transcript": transcript.text if transcript else None,
        "summary": summary.content if summary else None,
        "tasks": [{"id": t.id, "title": t.title, "status": t.status, "assignee": t.assignee.username if t.assignee else "Unassigned"} for t in meeting.tasks]
    }


class ProcessRequest(BaseModel):
    filename: str
    title: str = "Untitled Meeting"
    meeting_id: Optional[int] = None

@app.post("/process_meeting")
def process_meeting(request: ProcessRequest, db: Session = Depends(get_db)):
    if request.meeting_id:
        # Update existing scheduled meeting
        meeting = db.query(database.Meeting).filter(database.Meeting.id == request.meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meeting.audio_path = request.filename
        meeting.status = "queued"
        # Update title if changed? Maybe keep original.
        db.commit()
        db.refresh(meeting)
        new_meeting = meeting
    else:
        # Create new meeting
        new_meeting = database.Meeting(title=request.title, audio_path=request.filename, status="queued")
        db.add(new_meeting)
        db.commit()
        db.refresh(new_meeting)

    # Orchestrator will pick this up automatically
    
    return {"message": "Processing queued", "meeting_id": new_meeting.id}

@app.post("/meetings/{meeting_id}/reprocess")
def reprocess_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(database.Meeting).filter(database.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Reset status to 'recorded' so Orchestrator picks it up again
    meeting.status = "recorded"
    db.commit()
    db.commit()
    return {"message": "Meeting queued for reprocessing"}

class ScheduleRequest(BaseModel):
    title: str
    date: datetime.datetime

@app.post("/meetings/schedule")
def schedule_meeting(request: ScheduleRequest, db: Session = Depends(get_db)):
    new_meeting = database.Meeting(
        title=request.title, 
        date=request.date, 
        status="scheduled",
        audio_path="" # No audio yet
    )
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)
    return {"message": "Meeting scheduled", "meeting_id": new_meeting.id}

# Helper to decode token for dependency
def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(database.User).filter(database.User.username == username).first()
    if user is None:
        raise credentials_exception
    return Token(access_token=token, token_type="bearer", user_id=user.id, role=user.role, full_name=user.full_name)

# --- Real-time Transcription Setup ---
# Initialize a lightweight model for real-time chunks
try:
    realtime_model = transcription.TranscriptionService(model_size="tiny", compute_type="int8")
    print("✅ Real-time model (tiny) loaded.")
except Exception as e:
    print(f"❌ Failed to load real-time model: {e}")
    realtime_model = None

@app.post("/transcribe_chunk")
def transcribe_chunk(file: UploadFile = File(...)):
    if not realtime_model:
        raise HTTPException(status_code=503, detail="Real-time model not available")
    
    try:
        # Save temp chunk
        temp_filename = f"data/temp_chunk_{file.filename}"
        with open(temp_filename, "wb+") as buffer:
            buffer.write(file.file.read())
            
        # Transcribe
        text = realtime_model.transcribe(temp_filename)
        
        # Cleanup
        try:
            import os
            os.remove(temp_filename)
        except:
            pass
            
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
