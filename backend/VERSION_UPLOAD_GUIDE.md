# Contract Version Upload Feature

## Overview

This feature allows you to upload new versions of existing contracts, enabling the Intent Drift detection to track how contracts change over time.

## API Endpoint

```
POST /api/contracts/{contract_id}/versions/upload
```

### Headers
- `Authorization: Bearer {JWT_TOKEN}`
- `Content-Type: multipart/form-data`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `contract_id` | UUID | Yes | The ID of the existing contract (in URL) |
| `file` | File | Yes | The new version file (PDF, DOCX, PNG, JPG, JPEG) |
| `changeDescription` | String | No | Description of what changed (default: "Version update") |

### Response (201 Created)

```json
{
  "message": "New contract version uploaded successfully",
  "contract": {
    "id": "contract-uuid",
    "originalFilename": "updated_contract.pdf",
    "contractType": "Service Agreement"
  },
  "version": {
    "id": "version-uuid",
    "versionNumber": 2,
    "changeDescription": "Updated payment terms",
    "createdAt": "2025-12-22T23:30:00Z"
  },
  "versionHistory": {
    "totalVersions": 2,
    "currentVersion": 2
  },
  "processingTime": 2.5
}
```

## Features

### 1. **Automatic Version Creation**
- Creates a new ContractVersion record with incremented version number
- Stores complete snapshot of the contract at that point in time

### 2. **Automatic Text Extraction**
- Extracts text from uploaded file (PDF, DOCX, or images with OCR)
- Updates contract with new content

### 3. **Automatic Metadata Extraction**
- Extracts party names, dates, contract value, etc.
- Updates contract metadata

### 4. **Automatic Intent Drift Detection**
- Automatically compares new version with previous version
- Detects changes in:
  - Contract intents
  - Obligations
  - Rights
  - Risk levels

### 5. **Automatic Clause & Intent Analysis**
- Extracts clauses from the new version
- Mines contract intents
- Runs in background to avoid blocking

## Usage Example

### Using cURL

```bash
# Get your JWT token first
TOKEN=$(curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin@123"}' \
  | jq -r '.token')

# Upload new version
curl -X POST http://localhost:8002/api/contracts/{CONTRACT_ID}/versions/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@modified_contract.pdf" \
  -F "changeDescription=Updated payment terms and liability clauses"
```

### Using Python (requests)

```python
import requests

# Login
login_response = requests.post('http://localhost:8002/api/auth/login', json={
    'email': 'admin@example.com',
    'password': 'Admin@123'
})
token = login_response.json()['token']

# Upload new version
contract_id = 'your-contract-uuid'
file_path = 'modified_contract.pdf'

with open(file_path, 'rb') as f:
    response = requests.post(
        f'http://localhost:8002/api/contracts/{contract_id}/versions/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': f},
        data={'changeDescription': 'Updated payment terms'}
    )

print(response.json())
```

### Using Frontend (JavaScript/React)

```javascript
const uploadNewVersion = async (contractId, file, changeDescription) => {
  const token = localStorage.getItem('token');

  const formData = new FormData();
  formData.append('file', file);
  formData.append('changeDescription', changeDescription);

  const response = await fetch(
    `http://localhost:8002/api/contracts/${contractId}/versions/upload`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );

  if (response.ok) {
    const result = await response.json();
    console.log('New version uploaded:', result);
    return result;
  } else {
    const error = await response.json();
    console.error('Upload failed:', error);
    throw new Error(error.message);
  }
};

// Usage
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];
await uploadNewVersion('contract-uuid', file, 'Updated liability terms');
```

## Workflow

1. **Upload Initial Contract** → Creates v1
2. **Modify Contract** (externally in Word, PDF editor, etc.)
3. **Upload New Version** → Creates v2
4. **System Automatically:**
   - Extracts text from new file
   - Creates version snapshot
   - Compares v1 vs v2 (Intent Drift Detection)
   - Extracts clauses and intents
5. **View Results:**
   - Check "Intent Drift" tab to see changes
   - Compare versions side-by-side

## Intent Drift Detection

After uploading a new version, the system automatically:

1. **Compares Intents**: Identifies added, removed, or modified contract intents
2. **Tracks Obligations**: Detects changes in obligations between versions
3. **Monitors Rights**: Identifies changes in contractual rights
4. **Calculates Risk Delta**: Compares risk scores between versions
5. **Generates Timeline**: Creates a drift timeline showing all changes

### Viewing Intent Drift

Navigate to the contract detail page → **Intent Drift** tab → **Compare Versions**

- Select **Baseline Version** (e.g., v1)
- Select **Comparison Version** (e.g., v2)
- View the drift analysis showing:
  - Overall drift score
  - Intent changes
  - Obligation changes
  - Right changes
  - Risk delta

## Testing

Use the provided test script:

```bash
cd django_backend
python test_version_upload.py
```

Update the script with your contract ID and JWT token to test the functionality.

## Error Handling

### Common Errors

| Error | Reason | Solution |
|-------|--------|----------|
| 404 Not Found | Contract doesn't exist | Verify contract ID is correct |
| 403 Forbidden | Contract belongs to another user | Check authentication token |
| 400 Bad Request (No file) | File not provided | Include file in request |
| 400 Bad Request (Unsupported type) | File type not allowed | Use PDF, DOCX, PNG, JPG, or JPEG |
| 413 Payload Too Large | File > 25MB | Reduce file size |
| 400 Bad Request (No text) | Text extraction failed | Ensure file has extractable text |

## Notes

- Maximum file size: **25MB**
- Supported formats: **PDF, DOCX, PNG, JPG, JPEG**
- OCR is performed automatically for images (requires Tesseract)
- Version numbers are auto-incremented (v1, v2, v3, ...)
- Drift detection runs automatically in the background
- Clause extraction and intent mining run asynchronously

## Related Endpoints

- `GET /api/contracts/{contract_id}/versions` - Get version history
- `POST /api/contracts/{contract_id}/versions/{version1_id}/compare/{version2_id}` - Compare two versions
- `GET /api/contracts/{contract_id}/drift/timeline` - Get drift timeline
