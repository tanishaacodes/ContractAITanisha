"""
Restore database from SQL backup
Usage: python restore_backup.py "path/to/backup.sql"
"""

import os
import sys
import subprocess

# Database credentials from settings
DB_NAME = os.environ.get('DB_NAME', 'contractai_db')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Vansh1707')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', '3306')

def restore_backup(sql_file_path):
    """Restore MySQL database from SQL file"""

    if not os.path.exists(sql_file_path):
        print(f"❌ ERROR: File not found: {sql_file_path}")
        return False

    print("\n" + "="*60)
    print("DATABASE RESTORE")
    print("="*60)
    print(f"Source File: {sql_file_path}")
    print(f"Target DB:   {DB_NAME}")
    print(f"Host:        {DB_HOST}:{DB_PORT}")
    print(f"User:        {DB_USER}")
    print("="*60)

    # Confirm
    confirm = input("\n⚠️  This will REPLACE your current database. Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Aborted.")
        return False

    print("\n🔄 Restoring database...")

    # Build mysql command
    cmd = [
        'mysql',
        f'--host={DB_HOST}',
        f'--port={DB_PORT}',
        f'--user={DB_USER}',
        f'--password={DB_PASSWORD}',
        DB_NAME
    ]

    try:
        # Execute restore
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True
            )

        if result.returncode == 0:
            print("\n✅ SUCCESS! Database restored successfully!")
            print("\n" + "="*60)
            print("NEXT STEPS:")
            print("="*60)
            print("1. Restart your Django server")
            print("2. Refresh your browser")
            print("3. Run the What-If simulation")
            print("4. You should now see actual contract values!")
            print("="*60 + "\n")
            return True
        else:
            print(f"\n❌ ERROR: {result.stderr}")
            return False

    except FileNotFoundError:
        print("\n❌ ERROR: MySQL client not found in PATH")
        print("Please install MySQL client or add it to PATH")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore_backup.py \"path/to/backup.sql\"")
        print("\nExample:")
        print('python restore_backup.py "C:\\Users\\Admin\\Downloads\\contractai_backup (28).sql"')
        sys.exit(1)

    sql_file = sys.argv[1]
    success = restore_backup(sql_file)
    sys.exit(0 if success else 1)
