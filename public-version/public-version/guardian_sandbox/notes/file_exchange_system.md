# ΔΣ Guardian - File Exchange System

## Overview

Guardian now supports a complete file exchange system that allows users to upload files and Guardian to create downloadable files.

## Features

### User Upload Capabilities
- **Drag & Drop**: Users can drag files directly into the chat
- **Click to Upload**: Users can click the "📎 Attach" button to select files
- **File Types Supported**: Images, documents, text files, etc.
- **Progress Tracking**: Real-time upload progress with visual feedback

### File Processing
- **Images**: Automatically sent to AI for analysis and insights
- **Other Files**: Stored in sandbox for Guardian to process
- **Preview**: Images show preview in chat
- **File Management**: Users can download or delete uploaded files

### Guardian File Creation
- **Downloadable Files**: Guardian can create files for users to download
- **Multiple Formats**: Text, HTML, JSON, CSV, etc.
- **Safe Storage**: All files stored in controlled sandbox environment
- **Direct Links**: Users get direct download links

## Directory Structure

```
guardian_sandbox/
├── uploads/          # Files uploaded by users
├── downloads/        # Files created by Guardian for download
├── notes/           # Guardian's notes and documentation
├── websites/        # Web projects
├── projects/        # Various projects
└── creative/        # Creative works

static/
└── images/          # Images for AI analysis
```

## API Endpoints

### Upload
- `POST /api/upload-file` - Upload files
- `POST /api/analyze-image` - Analyze images with AI
- `POST /api/delete-file` - Delete uploaded files

### Download
- `GET /api/download/{file_path}` - Download files from sandbox

## Usage Examples

### User Uploads Image
1. User drags image into chat
2. Image uploaded to `static/images/`
3. AI analyzes image and provides insights
4. Image preview shown in chat
5. User can download or delete image

### User Uploads Document
1. User uploads document via drag & drop
2. Document stored in `guardian_sandbox/uploads/`
3. Guardian can read and process document
4. User can download or delete document

### Guardian Creates File
1. Guardian uses `create_downloadable_file()` tool
2. File created in `guardian_sandbox/downloads/`
3. Guardian provides download link to user
4. User clicks link to download file

## Security Features

- **Path Validation**: All file operations restricted to sandbox
- **File Type Checking**: Images vs other files handled differently
- **Authentication Required**: All endpoints require user authentication
- **Safe Filenames**: Automatic sanitization of filenames
- **Size Limits**: Built-in protection against large files

## Frontend Features

- **Visual Feedback**: Progress bars, success/error states
- **File Previews**: Image thumbnails in chat
- **Action Buttons**: Download, delete, analyze options
- **Responsive Design**: Works on desktop and mobile
- **Drag & Drop**: Intuitive file upload interface

## Integration with Guardian

Guardian can:
- Analyze uploaded images for emotional content
- Process uploaded documents for insights
- Create personalized files for users
- Generate reports, notes, or creative content
- Provide download links for created files

---

*Created by ΔΣ Guardian for Meranda and Stepan*
*Date: 2025-07-27* 