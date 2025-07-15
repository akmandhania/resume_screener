# Simple Resume Screening System Setup

## 🎉 No Google Cloud Setup Required!

This version works with just your Google Drive and direct file uploads - no complex Google Cloud Project setup needed.

## 🚀 Quick Start (2 minutes)

### 1. Install Dependencies
```bash
uv sync
```

### 2. Set OpenAI API Key
```bash
# Create .env file
echo "OPENAI_API_KEY=your-openai-key-here" > .env
```

### 3. Run the Application
```bash
uv run python simple_gladio_app.py
```

That's it! The web interface will be available at `http://localhost:7860`

## 📁 Two Ways to Use

### Option A: Direct File Upload
1. Upload your resume file (PDF, DOCX, or TXT) directly
2. Enter the job description
3. Click "Analyze Resume"

### Option B: Public Google Drive Link
1. Upload your resume to Google Drive
2. Right-click → "Get link"
3. Change sharing to "Anyone with the link can view"
4. Paste the link in the interface
5. Enter the job description
6. Click "Analyze Resume"

## 🔧 What's Different?

### ✅ What You DON'T Need:
- Google Cloud Project
- OAuth 2.0 credentials
- API keys setup
- Complex configuration

### ✅ What You DO Need:
- OpenAI API key (for AI analysis)
- Resume file or public Google Drive link
- Job description

## 🆚 Comparison

| Feature | Full Version | Simple Version |
|---------|-------------|----------------|
| Google Cloud Setup | Required | Not needed |
| File Upload | ✅ | ✅ |
| Google Drive Links | Private + Public | Public only |
| Setup Time | 15-30 minutes | 2 minutes |
| Functionality | Full | Same AI analysis |

## 🚨 Important Notes

### Google Drive Links
- **Must be public** (set to "Anyone with the link can view")
- Works with standard Google Drive sharing
- No authentication required

### File Types Supported
- **PDF**: Direct text extraction
- **DOCX**: Microsoft Word documents  
- **TXT**: Plain text files

### Limitations
- Google Drive links must be publicly accessible
- No access to private Google Drive files
- No automatic Google Sheets export (but data is prepared for manual export)

## 🎯 When to Use Each Version

### Use Simple Version If:
- You want to get started quickly
- You don't need private Google Drive access
- You prefer direct file uploads
- You don't need automated Google Sheets export

### Use Full Version If:
- You need private Google Drive access
- You want automated Google Sheets integration
- You're building a production system
- You need full API access

## 🔄 Switching Between Versions

You can have both versions installed:

```bash
# Simple version (no Google Cloud)
uv run python simple_gladio_app.py

# Full version (with Google Cloud)
uv run python gladio_app.py
```

## 🆘 Troubleshooting

### "File not found" Error
- Make sure Google Drive link is set to "Anyone with the link can view"
- Try uploading the file directly instead

### "Unsupported file type" Error
- Only PDF, DOCX, and TXT files are supported
- Convert your file to one of these formats

### OpenAI API Error
- Check that your OpenAI API key is set correctly
- Verify you have sufficient API credits

## 🎉 That's It!

The simple version gives you the same powerful AI resume screening without any complex setup. Perfect for quick testing or personal use! 