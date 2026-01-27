import sys
import os
import sqlite3

# Add project root to path for imports if needed (though we use raw sqlite here)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "gym_database.db")

def migrate():
    print(f"Migrating database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database not found. Nothing to migrate (init_db will handle it).")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(membros)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "observacoes" in columns:
            print("Column 'observacoes' already exists in 'membros'.")
        else:
            print("Adding column 'observacoes' to 'membros'...")
            cursor.execute("ALTER TABLE membros ADD COLUMN observacoes TEXT")
            conn.commit()
            print("Migration successful.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
