"""
StrokeSpeak - Update Video URLs in MySQL
Safely links newly generated tutorial videos to corresponding lessons:
- Lesson 339 (Sanskrit 'अ'): /api/v1/lessons/339/video
- Lesson 55 (Tamil 'அ'): /api/v1/lessons/55/video
- Lesson 223 (Tamil 'அ'): /api/v1/lessons/223/video
- Lesson 348 (Chinese '一'): /api/v1/lessons/348/video
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.db.database import get_db_connection

def main():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    updates = [
        (339, "/api/v1/lessons/339/video", "ready"),
        (55, "/api/v1/lessons/55/video", "ready"),
        (223, "/api/v1/lessons/223/video", "ready"),
        (348, "/api/v1/lessons/348/video", "ready"),
    ]
    
    for lesson_id, video_url, status in updates:
        sql = """
            UPDATE learning_lessons 
            SET tutorial_video_url = %s, tutorial_video_status = %s 
            WHERE id = %s
        """
        cursor.execute(sql, (video_url, status, lesson_id))
        print(f"Updated Lesson {lesson_id}: url={video_url}, status={status}")
        
    conn.commit()
    
    # Verify
    print("\nVerification:")
    cursor.execute("SELECT id, title, tutorial_video_url, tutorial_video_status FROM learning_lessons WHERE id IN (61, 339, 55, 223, 348)")
    for row in cursor.fetchall():
        print(f"  Lesson {row['id']} ({row['title']}): status={row['tutorial_video_status']}, url={row['tutorial_video_url']}")
        
    cursor.close()
    conn.close()
    print("\nDatabase update completed successfully.")

if __name__ == "__main__":
    main()
