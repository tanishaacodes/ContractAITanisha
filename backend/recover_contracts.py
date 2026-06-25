"""
Recover contracts from uploads directory
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, User
from api.utils import extract_text_from_file
import datetime


def recover_contracts():
    """Scan uploads directory and recover contracts"""
    print("\n" + "="*60)
    print("RECOVER CONTRACTS FROM UPLOADS DIRECTORY")
    print("="*60)

    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')

    # Get admin user
    admin_user = User.objects.filter(email='admin@example.com').first()
    if not admin_user:
        print("[ERROR] Admin user not found!")
        return

    # Get all files from uploads directory
    files = []
    for filename in os.listdir(uploads_dir):
        filepath = os.path.join(uploads_dir, filename)
        if os.path.isfile(filepath):
            # Skip very small files and images
            size = os.path.getsize(filepath)
            if size > 50000:  # Files larger than 50KB
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.pdf', '.docx', '.doc']:
                    mtime = os.path.getmtime(filepath)
                    files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': size,
                        'ext': ext,
                        'mtime': datetime.datetime.fromtimestamp(mtime)
                    })

    # Sort by modification time (oldest first)
    files.sort(key=lambda x: x['mtime'])

    print(f"\n[INFO] Found {len(files)} contract files in uploads/")

    # Show first 20 files with content preview
    print("\n[INFO] Showing files (sorted by upload date):")
    print("="*60)

    recoverable = []
    for idx, file_info in enumerate(files[:30], 1):
        try:
            # Extract text preview
            text_data = extract_text_from_file(file_info['filepath'], file_info['ext'])
            text = text_data.get('text', '')
            preview = text[:200].replace('\n', ' ').strip() if text else '[No text extracted]'

            print(f"\n{idx}. {file_info['filename']}")
            print(f"   Size: {file_info['size'] // 1024}KB")
            print(f"   Date: {file_info['mtime']}")
            print(f"   Preview: {preview}...")

            recoverable.append({**file_info, 'text': text})

        except Exception as e:
            print(f"\n{idx}. {file_info['filename']}")
            print(f"   [ERROR] Could not extract: {e}")

    print("\n" + "="*60)
    print("\n[NEXT STEP] Review the files above and identify your 5 contracts.")
    print("Then create a file 'contracts_to_recover.txt' with the line numbers.")
    print("\nExample contents of contracts_to_recover.txt:")
    print("1")
    print("3")
    print("7")
    print("12")
    print("15")
    print("="*60)


if __name__ == '__main__':
    try:
        recover_contracts()
    except Exception as e:
        print(f"\n\n[ERROR] Recovery failed: {e}")
        import traceback
        traceback.print_exc()
