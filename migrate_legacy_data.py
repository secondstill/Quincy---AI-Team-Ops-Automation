import sqlite3
import shutil
import os
from datetime import datetime

# Paths
OLD_DB = "data/quincy.db"
NEW_DB = "data/quincy_v2.db"

def migrate():
    if not os.path.exists(OLD_DB):
        print(f"❌ Old database not found at {OLD_DB}")
        return

    print(f"Migrating data from {OLD_DB} to {NEW_DB}...")

    # Connect to both
    old_conn = sqlite3.connect(OLD_DB)
    old_cur = old_conn.cursor()

    new_conn = sqlite3.connect(NEW_DB)
    new_cur = new_conn.cursor()

    # 1. Get Admin ID in New DB
    new_cur.execute("SELECT id FROM users WHERE username='admin'")
    admin_row = new_cur.fetchone()
    if not admin_row:
        print("❌ Admin user not found in new DB. Run 'python run.py' first.")
        return
    admin_id = admin_row[0]

    # 2. Migrate Meetings
    # Old schema: id, title, date, audio_path, status
    # New schema: id, title, date, audio_path, status (Same)
    old_cur.execute("SELECT id, title, date, audio_path, status FROM meetings")
    meetings = old_cur.fetchall()
    
    print(f"Found {len(meetings)} meetings to migrate.")

    for m in meetings:
        m_id, title, date, audio_path, status = m
        
        # Check if exists in new DB to avoid duplicates (by title and date roughly)
        new_cur.execute("SELECT id FROM meetings WHERE title=? AND date=?", (title, date))
        if new_cur.fetchone():
            print(f"  Skipping duplicate: {title}")
            continue

        print(f"  Migrating: {title}")
        # Insert Meeting
        new_cur.execute(
            "INSERT INTO meetings (title, date, audio_path, status) VALUES (?, ?, ?, ?)",
            (title, date, audio_path, status)
        )
        new_meeting_id = new_cur.lastrowid

        # ASSIGN TO ADMIN (populate meeting_participants)
        new_cur.execute(
            "INSERT INTO meeting_participants (meeting_id, user_id) VALUES (?, ?)",
            (new_meeting_id, admin_id)
        )

        # 3. Migrate Related Data (Transcript, Summary, Tasks)
        # Transcripts
        old_cur.execute("SELECT text FROM transcripts WHERE meeting_id=?", (m_id,))
        tr_row = old_cur.fetchone()
        if tr_row:
            new_cur.execute("INSERT INTO transcripts (meeting_id, text) VALUES (?, ?)", (new_meeting_id, tr_row[0]))

        # Summaries
        old_cur.execute("SELECT content FROM summaries WHERE meeting_id=?", (m_id,))
        sm_row = old_cur.fetchone()
        if sm_row:
            new_cur.execute("INSERT INTO summaries (meeting_id, content) VALUES (?, ?)", (new_meeting_id, sm_row[0]))

        # Tasks
        # Old task: id, meeting_id, title, description, assigned_to, status...
        # We map old assignments to NULL (Unassigned) because User IDs might have changed, 
        # unless we strictly map usernames. For simplicty, let's mark unassigned or assign to admin.
        # Let's assign to admin for visibility.
        old_cur.execute("SELECT title, description, status, priority FROM tasks WHERE meeting_id=?", (m_id,))
        tasks = old_cur.fetchall()
        for t in tasks:
            title, desc, status, prio = t
            new_cur.execute(
                "INSERT INTO tasks (meeting_id, title, description, assigned_to, status, priority) VALUES (?, ?, ?, ?, ?, ?)",
                (new_meeting_id, title, desc, admin_id, status, prio)
            )

    new_conn.commit()
    old_conn.close()
    new_conn.close()
    print("✅ Migration Complete!")

if __name__ == "__main__":
    migrate()
