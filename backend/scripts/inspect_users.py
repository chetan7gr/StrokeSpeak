import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.database import get_db_connection

def inspect_users_structure():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    print("=== USERS TABLE STRUCTURE ===")
    cursor.execute("DESCRIBE users")
    for col in cursor.fetchall():
        print(f"Column: {col['Field']:<15} | Type: {col['Type']:<15} | Null: {col['Null']:<5} | Key: {col['Key']:<5} | Default: {str(col['Default']):<10}")
        
    print("\n=== INDEXES & UNIQUE KEYS ===")
    cursor.execute("SHOW INDEX FROM users")
    for idx in cursor.fetchall():
        print(f"Index: {idx['Key_name']:<15} | Column: {idx['Column_name']:<15} | Non_unique: {idx['Non_unique']}")
        
    print("\n=== EXISTING USERS ===")
    cursor.execute("SELECT id, name, email, created_at FROM users ORDER BY id ASC")
    for u in cursor.fetchall():
        print(f"ID: {u['id']} | Name: {u['name']} | Email: {u['email']} | Created: {u['created_at']}")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_users_structure()
