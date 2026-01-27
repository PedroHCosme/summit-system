#!/usr/bin/env python3
"""
Migration script to add quota plan columns to the planos table.

Run this script to add the is_quota and quota_amount columns to existing databases.

Usage:
    python scripts/migrate_quota_plans.py
"""

import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'gym_database.db')

def run_migration():
    """Add is_quota and quota_amount columns to planos table if they don't exist."""
    print(f"Connecting to database: {os.path.abspath(DB_PATH)}")
    
    if not os.path.exists(DB_PATH):
        print("Database file not found. Run the application first to create it.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(planos)")
        columns = [row[1] for row in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'is_quota' not in columns:
            migrations_needed.append(
                "ALTER TABLE planos ADD COLUMN is_quota BOOLEAN DEFAULT 0"
            )
            print("  - Adding 'is_quota' column...")
        else:
            print("  - 'is_quota' column already exists")
        
        if 'quota_amount' not in columns:
            migrations_needed.append(
                "ALTER TABLE planos ADD COLUMN quota_amount INTEGER DEFAULT 0"
            )
            print("  - Adding 'quota_amount' column...")
        else:
            print("  - 'quota_amount' column already exists")
        
        if not migrations_needed:
            print("\n✓ Database is already up to date!")
            return True
        
        # Run migrations
        for sql in migrations_needed:
            cursor.execute(sql)
        
        conn.commit()
        print(f"\n✓ Successfully added {len(migrations_needed)} column(s)")
        
        # Now update existing Voucher plans to be quota-based
        cursor.execute("""
            UPDATE planos 
            SET is_quota = 1, quota_amount = 0 
            WHERE nome = 'Voucher' AND (is_quota IS NULL OR is_quota = 0)
        """)
        if cursor.rowcount > 0:
            print(f"  - Updated 'Voucher' plan to be quota-based")
        
        conn.commit()
        
        # Show current state
        print("\nCurrent planos table:")
        cursor.execute("SELECT nome, preco, is_quota, quota_amount FROM planos")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: preco={row[1]}, is_quota={row[2]}, quota_amount={row[3]}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Quota Plan Migration Script")
    print("=" * 50)
    print()
    
    success = run_migration()
    
    print()
    if success:
        print("Migration completed successfully!")
        print("\nNext step: Run 'python scripts/seed_plans.py' to add 'Pacote 10' plan")
    else:
        print("Migration failed. Please check the error messages above.")
    
    sys.exit(0 if success else 1)
