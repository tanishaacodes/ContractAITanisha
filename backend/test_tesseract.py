import os
import sys

# Add the project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

import pytesseract
from PIL import Image, ImageDraw, ImageFont

print("=" * 50)
print("Testing Tesseract Configuration")
print("=" * 50)

# Check tesseract path
print(f"\n1. Tesseract CMD path: {pytesseract.pytesseract.tesseract_cmd}")
print(f"   Exists: {os.path.exists(pytesseract.pytesseract.tesseract_cmd)}")

# Test tesseract version
try:
    version = pytesseract.get_tesseract_version()
    print(f"\n2. Tesseract version: {version}")
    print("   [OK] Tesseract is accessible!")
except Exception as e:
    print(f"\n2. ERROR getting version: {e}")
    print("   [ERROR] Tesseract is NOT accessible!")

# Create a simple test image with text
print("\n3. Creating test image with text...")
img = Image.new('RGB', (400, 100), color='white')
draw = ImageDraw.Draw(img)
draw.text((10, 30), "Hello Tesseract OCR!", fill='black')

# Save test image
test_image_path = os.path.join(os.path.dirname(__file__), 'test_image.png')
img.save(test_image_path)
print(f"   Saved to: {test_image_path}")

# Test OCR
print("\n4. Testing OCR on image...")
try:
    text = pytesseract.image_to_string(img)
    print(f"   Extracted text: '{text.strip()}'")
    if text.strip():
        print("   [OK] OCR is working!")
    else:
        print("   [WARNING] OCR returned empty text")
except Exception as e:
    print(f"   [ERROR] OCR failed: {e}")

print("\n" + "=" * 50)
print("Test complete!")
print("=" * 50)
