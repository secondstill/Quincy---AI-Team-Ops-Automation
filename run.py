import subprocess
import time
import sys
import os
from backend.database import init_db, SessionLocal, User, UserRole
from backend.auth import get_password_hash

def setup_initial_data():
    print("Initializing Database...")
    init_db()
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        print("Creating default admin user...")
        admin = User(
            username="admin", 
            hashed_password=get_password_hash("admin123"),
            full_name="System Admin",
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        print("Admin user created: admin / admin123")
    
    if not db.query(User).filter(User.username == "employee").first():
        print("Creating default employee user...")
        emp = User(
            username="employee", 
            hashed_password=get_password_hash("emp123"),
            full_name="John Doe",
            role=UserRole.EMPLOYEE
        )
        db.add(emp)
        db.commit()
        print("Employee user created: employee / emp123")
    db.close()

def main():
    # 1. Setup Data
    setup_initial_data()

    # 2. Start Backend
    print("Starting Backend (FastAPI)...")
    backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"])

    # 3. Start Orchestrator
    print("Starting Orchestrator (Agent)...")
    # We run this as a module to ensure imports work
    orchestrator = subprocess.Popen([sys.executable, "-m", "agent.orchestrator_runner"])

    # 4. Start Frontend
    print("Starting Frontend (Streamlit)...")
    frontend = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/app.py"])

    print("\n--- QUINCY IS RUNNING ---")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:8501")
    print("Login with: admin / admin123")
    print("-------------------------")

    try:
        backend.wait()
        frontend.wait()
        orchestrator.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend.terminate()
        frontend.terminate()
        orchestrator.terminate()

if __name__ == "__main__":
    main()
