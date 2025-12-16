from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import datetime
import enum

DATABASE_URL = "sqlite:///./data/quincy.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default=UserRole.EMPLOYEE)

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    audio_path = Column(String)
    status = Column(String, default="recorded") # recorded, processing, completed

    transcript = relationship("Transcript", back_populates="meeting", uselist=False)
    summary = relationship("Summary", back_populates="meeting", uselist=False)
    tasks = relationship("Task", back_populates="meeting")

class Transcript(Base):
    __tablename__ = "transcripts"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    text = Column(Text)
    
    meeting = relationship("Meeting", back_populates="transcript")

class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    content = Column(Text)
    
    meeting = relationship("Meeting", back_populates="summary")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    title = Column(String)
    description = Column(Text)
    assigned_to = Column(Integer, ForeignKey("users.id")) # User ID
    status = Column(String, default=TaskStatus.PENDING)
    due_date = Column(DateTime, nullable=True)
    priority = Column(String, default="Medium")

    meeting = relationship("Meeting", back_populates="tasks")
    assignee = relationship("User")

def init_db():
    Base.metadata.create_all(bind=engine)
