import os
import sys
import requests
from PIL import Image, ImageDraw

# Configuration
BASE_URL = 'http://localhost:8000'
API_URL = f'{BASE_URL}/api'

# Test credentials
EMAIL = 'admin@example.com'
PASSWORD = 'admin123'  # Try common admin password

print("=" * 50)
print("Testing Image Upload with Tesseract OCR")
print("=" * 50)

# Step 1: Create a test image with text
print("\n1. Creating test image...")
img = Image.new('RGB', (600, 200), color='white')
draw = ImageDraw.Draw(img)

# Draw some text that looks like a contract
contract_text = """
EMPLOYMENT AGREEMENT
This agreement is between Company and Employee
Dated: January 1, 2024
"""
draw.text((20, 20), contract_text.strip(), fill='black')

# Save test image
test_image_path = 'test_contract_image.png'
img.save(test_image_path)
print(f"   Created: {test_image_path}")

# Step 2: Login
print("\n2. Logging in...")
try:
    response = requests.post(
        f'{API_URL}/auth/login',
        json={'email': EMAIL, 'password': PASSWORD}
    )

    if response.status_code == 200:
        token = response.json().get('token')
        print(f"   [OK] Login successful!")
        print(f"   Token: {token[:20]}...")
    else:
        print(f"   [ERROR] Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        print("\n   Trying to create/reset admin user...")

        # Try to reset admin password using Django
        os.system('cd django_backend && python -c "from core.models import User; u = User.objects.get(email=\'admin@example.com\'); u.set_password(\'admin123\'); u.save(); print(\'Password reset\')"')

        # Try login again
        response = requests.post(
            f'{API_URL}/auth/login',
            json={'email': EMAIL, 'password': PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get('token')
            print(f"   [OK] Login successful after reset!")
        else:
            print(f"   [ERROR] Still failed: {response.text}")
            sys.exit(1)

except Exception as e:
    print(f"   [ERROR] Login error: {e}")
    sys.exit(1)

# Step 3: Upload the image
print("\n3. Uploading test image...")
try:
    with open(test_image_path, 'rb') as f:
        files = {'file': (test_image_path, f, 'image/png')}
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.post(
            f'{API_URL}/contracts/upload',
            files=files,
            headers=headers
        )

    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"   [OK] Upload successful!")
        print(f"\n   Results:")
        print(f"   - Contract ID: {result.get('contractId')}")
        print(f"   - File Type: {result.get('type')}")
        print(f"   - OCR Performed: {result.get('ocr_performed')}")
        print(f"   - Contract Type: {result.get('contractType')}")
        print(f"   - Extracted Text Length: {len(result.get('full_text', ''))}")
        print(f"   - Text Preview: {result.get('text_preview', '')[:100]}...")
    else:
        print(f"   [ERROR] Upload failed!")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"   [ERROR] Upload error: {e}")

print("\n" + "=" * 50)
print("Test complete!")
print("=" * 50)

# Cleanup
if os.path.exists(test_image_path):
    os.remove(test_image_path)
    print(f"Cleaned up: {test_image_path}")
