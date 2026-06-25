import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.utils import extract_text_from_file, perform_ocr_on_pdf, extract_text_from_pdf_js

# Test the LOI PDF
pdf_path = 'uploads/1765958877361-LOI_Acknowledgement(1).pdf'

print("=" * 60)
print("Testing LOI Acknowledgement PDF Extraction")
print("=" * 60)

# Test 1: PDF.js extraction
print("\n1. Testing PDF.js extraction...")
pdf_js_result = extract_text_from_pdf_js(pdf_path)
print(f"   Pages detected: {pdf_js_result.get('pages')}")
print(f"   Text length: {len(pdf_js_result.get('text', ''))}")
print(f"   Text preview: {pdf_js_result.get('text', '')[:200]}")

# Test 2: OCR extraction
print("\n2. Testing OCR extraction...")
try:
    ocr_result = perform_ocr_on_pdf(pdf_path, max_pages=7)
    print(f"   OCR performed: {ocr_result.get('ocr_performed')}")
    print(f"   Pages processed: {ocr_result.get('pages')}")
    print(f"   Text length: {len(ocr_result.get('text', ''))}")
    print(f"   Error (if any): {ocr_result.get('error')}")
    if ocr_result.get('text'):
        print(f"   Text preview: {ocr_result.get('text')[:500]}")
except Exception as e:
    print(f"   OCR Error: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 3: Full extraction (should use improved logic)
print("\n3. Testing full extract_text_from_file...")
try:
    full_result = extract_text_from_file(pdf_path, '.pdf')
    print(f"   OCR performed: {full_result.get('ocr_performed')}")
    print(f"   Pages: {full_result.get('pages')}")
    print(f"   Text length: {len(full_result.get('text', ''))}")
    if full_result.get('text'):
        print(f"   Text preview: {full_result.get('text')[:500]}")
except Exception as e:
    print(f"   Extraction Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
