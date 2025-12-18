
import os
import sys
import traceback

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.data.database_manager import DatabaseManager
from src.data.google_sheets_service import GoogleSheetsService
from src.config import CREDENTIALS_PATH, SPREADSHEET_ID

def debug_sync():
    print("--- SYNC DEBUG START ---")
    
    # 1. Test Database Connection
    print("\n[1] Testing Database Connection...")
    try:
        db = DatabaseManager()
        if db.connect():
            print("✅ Database connection successful.")
            # Check table count
            cursor = db.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   Tables found: {[t[0] for t in tables]}")
            
            # Check member count
            if 'membros' in [t[0] for t in tables]:
                cursor.execute("SELECT COUNT(*) FROM membros")
                count = cursor.fetchone()[0]
                print(f"   Members count: {count}")
            else:
                print("   ⚠️ Table 'membros' not found.")
            db.close()
        else:
            print("❌ Database connection FAILED.")
    except Exception as e:
        print(f"❌ Database Exception: {e}")
        traceback.print_exc()

    # 2. Test Google Sheets Auth
    print("\n[2] Testing Google Sheets Authentication...")
    print(f"   Credentials Path: {CREDENTIALS_PATH}")
    if not os.path.exists(CREDENTIALS_PATH):
        print("❌ Credentials file NOT FOUND.")
    else:
        try:
            service = GoogleSheetsService(CREDENTIALS_PATH)
            if service.authenticate():
                print("✅ Authentication successful.")
                
                # 3. Test Reading Spreadsheet
                print("\n[3] Testing Spreadsheet Read...")
                print(f"   Spreadsheet ID: {SPREADSHEET_ID}")
                try:
                    # Try reading metadata or first sheet
                    # We'll try reading a known range from 'Jan/25' or just metadata
                    # GoogleSheetsService.read_spreadsheet takes (spreadsheet_id, range_name, sheet_name)
                    # Let's try reading the first row of 'Jan/25'
                    data = service.read_spreadsheet(SPREADSHEET_ID, 'A1:B1', 'Jan/25')
                    if data is not None:
                        print(f"✅ Read successful. Data received: {data}")
                    else:
                        print("⚠️ Read returned None (might be empty or error caught inside service).")
                except Exception as e:
                    print(f"❌ Spreadsheet Read Exception: {e}")
                    traceback.print_exc()
            else:
                print("❌ Authentication FAILED (service.authenticate returned False).")
        except Exception as e:
            print(f"❌ Auth Exception: {e}")
            traceback.print_exc()

    print("\n--- SYNC DEBUG END ---")

if __name__ == "__main__":
    debug_sync()
