"""
Fetch latest practice attempt result from MySQL
"""
import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.db.database import get_db_connection

def fetch_latest():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT pa.id, pa.user_id, pa.character_id, c.character_text, c.pronunciation_text,
               pa.handwriting_score, pa.stroke_order_score, pa.pronunciation_score,
               pa.feedback, pa.created_at, pa.pronunciation_status, pa.transcribed_text,
               pa.pronunciation_feedback,
               LENGTH(pa.stroke_data) as stroke_bytes,
               LENGTH(pa.audio_data) as audio_bytes
        FROM practice_attempts pa
        LEFT JOIN characters c ON c.id = pa.character_id
        ORDER BY pa.id DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    
    if not row:
        print("No practice attempts found.")
        return None
        
    print("=" * 60)
    print(f"LATEST PRACTICE ATTEMPT: #{row['id']}")
    print("=" * 60)
    print(f"User ID: {row['user_id']}")
    print(f"Character: {row['character_id']} ('{row['character_text']}') - Pronunciation target: '{row['pronunciation_text']}'")
    print(f"Timestamp: {row['created_at']}")
    print(f"\n[HANDWRITING METRICS]")
    print(f"  Geometry Accuracy: {row['handwriting_score']}%" if row['handwriting_score'] is not None else "  Geometry Accuracy: N/A")
    print(f"  Stroke-Order Score: {row['stroke_order_score']}%" if row['stroke_order_score'] is not None else "  Stroke-Order Score: N/A")
    print(f"  Stroke Data Size: {row['stroke_bytes']} bytes")
    print(f"  Handwriting Feedback: {row['feedback']}")
    print(f"\n[SPEECH METRICS]")
    print(f"  Pronunciation Score: {row['pronunciation_score']}%" if row['pronunciation_score'] is not None else "  Pronunciation Score: N/A")
    print(f"  Pronunciation Status: {row['pronunciation_status']}")
    print(f"  Transcribed Text (Whisper): '{row['transcribed_text']}'")
    print(f"  Speech Audio Size: {row['audio_bytes']} bytes")
    print(f"  Speech Feedback: {row['pronunciation_feedback']}")
    print("=" * 60)
    
    cursor.close()
    conn.close()
    return row

if __name__ == "__main__":
    fetch_latest()
