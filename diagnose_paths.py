
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from src.config import CREDENTIALS_PATH
except ImportError:
    # Fallback if src is not in path correctly or config fails
    project_dir = os.path.dirname(os.path.abspath(__file__))
    CREDENTIALS_PATH = os.path.join(project_dir, 'credentials.json')

def diagnose():
    print("--- DIAGNOSTIC REPORT ---")
    
    # 1. Current Working Directory
    cwd = os.getcwd()
    print(f"Current Working Directory: {cwd}")
    
    # 2. Project Root (assumed based on this script location)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script Directory (Project Root): {script_dir}")
    
    # 3. Credentials
    print(f"\n[Credentials]")
    print(f"Expected Path: {CREDENTIALS_PATH}")
    if os.path.exists(CREDENTIALS_PATH):
        print("✅ Found 'credentials.json' at expected path.")
    else:
        print("❌ 'credentials.json' NOT FOUND at expected path.")
        # Check if it exists in src/
        src_creds = os.path.join(script_dir, 'src', 'credentials.json')
        if os.path.exists(src_creds):
            print(f"⚠️ Found 'credentials.json' in 'src/' ({src_creds}). Config expects it in root.")
        else:
            print("❌ 'credentials.json' NOT FOUND in 'src/' either.")

    # 4. Database
    print(f"\n[Database]")
    # Replicate DatabaseManager logic
    db_path_relative = "gym_database.db"
    db_path = os.path.join(script_dir, db_path_relative)
    
    print(f"Expected Path: {db_path}")
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ Found 'gym_database.db'. Size: {size} bytes.")
        if size == 0:
            print("⚠️ Database file is empty (0 bytes).")
    else:
        print("❌ 'gym_database.db' NOT FOUND at expected path.")
        # Check if it exists in src/
        src_db = os.path.join(script_dir, 'src', 'gym_database.db')
        if os.path.exists(src_db):
            size = os.path.getsize(src_db)
            print(f"⚠️ Found 'gym_database.db' in 'src/' ({src_db}). Size: {size} bytes. Code expects it in root.")
        else:
            print("❌ 'gym_database.db' NOT FOUND in 'src/' either.")

    print("\n--- END REPORT ---")

if __name__ == "__main__":
    diagnose()
