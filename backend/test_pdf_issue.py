import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
import django
django.setup()

from PyPDF2 import PdfReader
from api.utils import extract_text_from_pdf_js, perform_ocr_on_pdf

# Test with the uploaded PDF
pdf_path = r"c:\Users\Admin\Desktop\contractaiphase2\django_backend\uploads\1767593066533-Signed_Contract.pdf"

print("=" * 80)
print("Testing PDF extraction...")
print("=" * 80)

# Check if file exists
if not os.path.exists(pdf_path):
    print(f"ERROR: File not found: {pdf_path}")
    sys.exit(1)

print(f"\n1. File size: {os.path.getsize(pdf_path)} bytes")

# Test basic PyPDF2 extraction
print("\n2. Testing PyPDF2 extraction...")
try:
    result = extract_text_from_pdf_js(pdf_path)
    text = result.get('text', '')
    pages = result.get('pages')

    print(f"   - Pages: {pages}")
    print(f"   - Extracted text length: {len(text)}")
    print(f"   - Text preview (first 500 chars):")
    print("   " + "-" * 70)
    print("   " + text[:500].replace("\n", "\n   "))
    print("   " + "-" * 70)

    if len(text.strip()) < 5:
        print("\n   WARNING: Insufficient text extracted!")

    # Check expected minimum
    min_expected = (pages or 1) * 200
    actual = len(text.strip())
    print(f"\n   - Expected minimum chars: {min_expected}")
    print(f"   - Actual chars: {actual}")

    if actual < min_expected:
        print("\n3. Testing OCR fallback...")
        ocr_result = perform_ocr_on_pdf(pdf_path)
        ocr_text = ocr_result.get('text', '')
        print(f"   - OCR text length: {len(ocr_text)}")
        print(f"   - OCR text preview (first 500 chars):")
        print("   " + "-" * 70)
        print("   " + ocr_text[:500].replace("\n", "\n   "))
        print("   " + "-" * 70)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test complete")
print("=" * 80)
