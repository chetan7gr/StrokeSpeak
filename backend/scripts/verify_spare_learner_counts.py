import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.db.database import get_db_connection

def verify_counts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Check practice_attempts count
    cursor.execute("SELECT count(*) as cnt FROM practice_attempts")
    pa_cnt = cursor.fetchone()['cnt']
    
    # 2. Check lesson_progress count
    cursor.execute("SELECT count(*) as cnt FROM lesson_progress")
    lp_cnt = cursor.fetchone()['cnt']
    
    # 3. Check new user (id=3) rows
    cursor.execute("SELECT count(*) as cnt FROM practice_attempts WHERE user_id = 3")
    user3_pa = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT count(*) as cnt FROM lesson_progress WHERE user_id = 3")
    user3_lp = cursor.fetchone()['cnt']
    
    # 4. Check total users
    cursor.execute("SELECT count(*) as cnt FROM users")
    users_cnt = cursor.fetchone()['cnt']
    
    print(f"Total Users count: {users_cnt}")
    print(f"Total practice_attempts count: {pa_cnt} (Expected: 88)")
    print(f"Total lesson_progress count: {lp_cnt} (Expected: 12)")
    print(f"User 3 (Spare Demo Learner) practice_attempts: {user3_pa} (Expected: 0)")
    print(f"User 3 (Spare Demo Learner) lesson_progress: {user3_lp} (Expected: 0)")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    verify_counts()
