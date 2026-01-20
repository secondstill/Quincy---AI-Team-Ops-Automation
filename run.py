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
    # Bind to 0.0.0.0 to expose to LAN
    backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

    # 3. Start Orchestrator
    print("Starting Orchestrator (Agent)...")
    # We run this as a module to ensure imports work
    orchestrator = subprocess.Popen([sys.executable, "-m", "agent.orchestrator_runner"])

    # 4. Start Frontend
    print("Starting Frontend (Next.js)...")
    
    # Try to find npm
    npm_cmd = "npm"
    possible_paths = [
        r"C:\Program Files\nodejs\npm.cmd",
        r"C:\Program Files\nodejs\npm",
    ]
    
    # Check if npm is in PATH (simple check)
    import shutil
    if not shutil.which("npm"):
        # Not in path, check common locations
        for p in possible_paths:
            if os.path.exists(p):
                npm_cmd = p
                print(f"Using absolute npm path: {npm_cmd}")
                break
    
    # Use shell=True for Windows compatibility with batch files if just 'npm', 
    # but if we have full path to .cmd, we can use it directly or with shell=True.
    # Bind Next.js to 0.0.0.0
    frontend = subprocess.Popen([npm_cmd, "run", "dev", "--", "-H", "0.0.0.0"], cwd="frontend-next", shell=True)

    print("\n--- QUINCY IS RUNNING ---")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:3000")
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
