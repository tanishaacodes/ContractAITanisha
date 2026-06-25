# Upload Contract Version - UI Guide

## Overview

The frontend now includes a complete UI for uploading new versions of existing contracts, enabling the Intent Drift feature to work properly.

## Location

The upload version feature is available in the **Contract Details** page, specifically in the **Version History** tab.

## How to Use

### Step 1: Navigate to Contract Details
1. Go to **My Contracts**
2. Click on any contract to view its details
3. Click on the **Version History** tab

### Step 2: Upload New Version
1. Click the **"Upload New Version"** button (blue button in top-right)
2. A modal will appear with:
   - **File selection** (accepts PDF, DOCX, PNG, JPG, JPEG)
   - **Change description** field (optional)
   - Information about what happens after upload

### Step 3: Select File and Describe Changes
1. Click **"Choose File"** and select your updated contract
2. Optionally, describe what changed (e.g., "Updated payment terms and liability clauses")
3. Click **"Upload Version"**

### Step 4: Wait for Processing
- The upload may take a few seconds depending on file size
- You'll see a success message when complete
- The modal will automatically close after 2 seconds

### Step 5: View Results
After upload:
- **Version History** tab will automatically refresh showing the new version
- **Intent Drift** tab will have the new version available for comparison
- Background processing starts:
  - Text extraction
  - Clause extraction
  - Intent mining
  - Drift detection (comparing old vs new version)

## UI Components Added

### 1. **Upload Button** (Version History Tab)
- Located at top-right of Version History section
- Blue button with upload icon
- Opens upload modal when clicked

### 2. **Upload Modal**
- **File Input**: Styled file picker with drag-and-drop support
- **Description Input**: Multi-line text area for change notes
- **File Info**: Shows selected file name and size
- **Error/Success Messages**: Clear feedback on upload status
- **Info Box**: Explains what happens after upload
- **Action Buttons**:
  - **Upload Version**: Primary action (disabled until file selected)
  - **Cancel**: Closes modal without uploading

### 3. **Real-time Feedback**
- Loading states during upload
- Success messages with version number
- Error messages if upload fails
- File size validation (max 25MB)
- File type validation (only allowed formats)

## File Modifications

### Modified Files:
1. **[frontend/src/pages/ContractDetails.jsx](frontend/src/pages/ContractDetails.jsx)**
   - Added upload modal state management
   - Added `handleUploadVersion` function
   - Added "Upload New Version" button in versions tab
   - Added modal UI with form and validation
   - Added import for `Upload` and `X` icons from lucide-react

2. **[frontend/src/components/VersionHistory.jsx](frontend/src/components/VersionHistory.jsx)**
   - Added `refreshKey` prop to trigger reload
   - Updated useEffect dependency array

## Features

### ✅ File Validation
- Accepts: PDF, DOCX, PNG, JPG, JPEG
- Maximum size: 25MB
- Shows file info after selection

### ✅ User Feedback
- Real-time upload progress
- Success/error messages
- Automatic modal closure on success
- Disabled states during processing

### ✅ Auto-refresh
- Version history automatically updates
- New version immediately available in drift comparison

### ✅ Responsive Design
- Modal centered on screen
- Overlay background
- Mobile-friendly layout

## Example Workflow

1. **User has Contract v1** uploaded
2. **User edits contract** externally (in Word, PDF editor, etc.)
3. **User goes to Version History** tab
4. **User clicks "Upload New Version"**
5. **User selects modified file** and enters "Updated payment terms"
6. **User clicks "Upload Version"**
7. **System creates v2** and triggers analysis
8. **User sees success message** "✅ Version 2 uploaded successfully!"
9. **Version History refreshes** showing both v1 and v2
10. **User switches to Intent Drift** tab
11. **User selects v1 vs v2** for comparison
12. **System shows drift analysis** with all changes

## Screenshots (Conceptual)

### Version History Tab
```
┌─────────────────────────────────────────────────┐
│ Version History            [Upload New Version] │ ← Button
├─────────────────────────────────────────────────┤
│ v1 - 12/22/2025                                 │
│ ├─ Initial upload                               │
│ └─ Created by: admin@example.com                │
└─────────────────────────────────────────────────┘
```

### Upload Modal
```
┌───────────────────────────────────────┐
│ Upload New Version               [×]  │
├───────────────────────────────────────┤
│ Select File (PDF, DOCX, PNG, ...)    │
│ [Choose File] contract_v2.pdf         │
│ Selected: contract_v2.pdf (2.3 MB)    │
│                                       │
│ Change Description (Optional)         │
│ ┌───────────────────────────────────┐ │
│ │ Updated payment terms and         │ │
│ │ liability clauses                 │ │
│ └───────────────────────────────────┘ │
│                                       │
│ ℹ️ What happens after upload:        │
│ • Creates new version (v2, v3, ...)  │
│ • Triggers intent drift detection    │
│ • Extracts clauses and intents       │
│ • Compares with previous version     │
│                                       │
│ [Upload Version]  [Cancel]           │
└───────────────────────────────────────┘
```

## API Integration

The UI calls:
```javascript
POST /api/contracts/{contractId}/versions/upload
```

With:
- `file`: The selected file
- `changeDescription`: Optional description text

Returns:
- Version number
- Total versions count
- Processing time

## Error Handling

The UI handles:
- ❌ No file selected
- ❌ File too large (>25MB)
- ❌ Unsupported file type
- ❌ Network errors
- ❌ Server errors
- ❌ Authentication errors

All errors are displayed in the modal with clear messages.

## Styling

- Uses Tailwind CSS classes
- Matches existing app design
- Dark theme (slate-800/900)
- Blue accent colors for actions
- Red for errors, green for success

## Next Steps

After uploading a new version, users can:
1. View version history
2. Compare versions in Intent Drift tab
3. See drift timeline
4. Analyze changes in intents, obligations, rights
5. View risk delta between versions

---

**The Intent Drift feature is now fully functional!** 🎉
