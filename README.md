# Resume Screening System with LangGraph and Gladio

A modern, AI-powered resume screening system that converts the original n8n workflow to a Python-based LangGraph implementation with a web interface.

## 🚀 Features

- **AI-Powered Analysis**: Uses GPT-4o-mini for intelligent resume screening
- **Multi-Format Support**: Handles PDF, DOCX, and TXT files
- **Google Drive Integration**: Direct processing from Google Drive links
- **Batch Processing**: Screen one resume against multiple job descriptions
- **Structured Output**: Detailed analysis with strengths, weaknesses, risk/reward assessment
- **Web Interface**: Beautiful Gradio-based UI (Gladio-compatible)
- **LangGraph Workflow**: State-based processing with clear data flow
- **Export Ready**: Prepared data for Google Sheets integration
- **Modern Package Management**: Uses `uv` for fast dependency resolution

## 📋 System Architecture

```
Input (Google Drive Link + Job Description)
    ↓
FileProcessorNode (Extract file info)
    ↓
TextExtractorNode (Extract text from file)
    ↓
ResumeScreenerNode (AI analysis)
    ↓
InfoExtractorNode (Extract candidate info)
    ↓
DataExporterNode (Prepare export data)
    ↓
Output (Structured results + Spreadsheet data)
```

## 🛠️ Setup Instructions

### 1. Install uv (Package Manager)

First, install `uv` if you haven't already:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

### 2. Quick Setup

Run the automated setup script:

```bash
python setup.py
```

This will:
- Install `uv` if not present
- Install all dependencies
- Create configuration files
- Set up convenience scripts

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Clone the repository
git clone <repository-url>
cd resume-screening-system

# Install dependencies
uv sync

# Create environment file
cp env_example.txt .env
```

### 4. Set Up Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Sheets API (optional)
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the credentials file
5. Rename the downloaded file to `credentials.json` and place it in the project root

### 5. Configure Environment Variables

Edit `.env` with your actual values:
```env
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 6. Run the Application

#### Single Job Screening (Simple Interface)
```bash
uv run python simple_gladio_app.py
```
The web interface will be available at `http://localhost:7860`

#### Batch Processing (Multiple Jobs)
```bash
uv run python batch_gladio_app.py
```
The batch interface will be available at `http://localhost:7861`

#### Full Google Cloud Integration
```bash
uv run python gladio_app.py
```
The full interface will be available at `http://localhost:7860`

## 📖 Usage Guide

### Basic Usage

1. **Prepare Your Resume**: Upload a resume to Google Drive and make it accessible via link
2. **Get the Link**: Right-click the file in Google Drive → "Get link" → Copy the link
3. **Open the Web Interface**: Navigate to `http://localhost:7860`
4. **Input Data**:
   - Paste the Google Drive link in the first field
   - Enter or modify the job description in the second field
5. **Analyze**: Click "Analyze Resume" to start the screening process
6. **Review Results**: View the detailed analysis and spreadsheet export preview

### Supported File Formats

- **PDF**: Direct text extraction
- **DOCX**: Microsoft Word documents
- **TXT**: Plain text files

### Google Drive Link Formats

The system supports these Google Drive link formats:
- `https://drive.google.com/file/d/FILE_ID/view`
- `https://drive.google.com/open?id=FILE_ID`

### Batch Processing Usage

For screening one resume against multiple job descriptions:

1. **Prepare Job URLs**: Create a CSV file with job URLs:
   ```csv
   Job URL
   https://www.linkedin.com/jobs/view/example1
   https://www.indeed.com/viewjob?jk=example2
   https://www.glassdoor.com/job-listing/example3
   ```

2. **Start Batch Interface**: Navigate to `http://localhost:7861`

3. **Upload Files**: 
   - Upload your resume file
   - Upload your job URLs CSV file

4. **Process**: Click "Start Batch Screening" to analyze all jobs

5. **Review Results**: View summary and download detailed CSV for Google Sheets

## 🔍 Analysis Output

The system provides comprehensive analysis including:

### Candidate Information
- First Name
- Last Name
- Email Address

### Screening Results
- **Strengths**: Matching qualifications and skills
- **Weaknesses**: Areas of concern or gaps
- **Risk Factor**: Assessment of hiring risks (Low/Medium/High)
- **Reward Factor**: Potential upside assessment (Low/Medium/High)
- **Overall Fit Rating**: 0-10 score with detailed justification

### Export Data
Structured data ready for Google Sheets integration with fields:
- Date
- Resume Link
- Candidate Info
- Analysis Results
- Risk/Reward Assessment
- Overall Rating

## 🏗️ Technical Details

### LangGraph Workflow

The system uses LangGraph's state-based workflow:

```python
class ResumeScreeningState(TypedDict):
    google_drive_link: str
    job_description: str
    file_id: Optional[str]
    file_name: Optional[str]
    file_type: Optional[str]
    resume_text: Optional[str]
    screening_results: Optional[Dict[str, Any]]
    candidate_info: Optional[Dict[str, str]]
    spreadsheet_data: Optional[Dict[str, Any]]
    error: Optional[str]
```

### Key Components

1. **FileProcessorNode**: Handles Google Drive link parsing and file metadata extraction
2. **TextExtractorNode**: Extracts text from various file formats
3. **ResumeScreenerNode**: AI-powered analysis using GPT-4o-mini
4. **InfoExtractorNode**: Extracts candidate contact information
5. **DataExporterNode**: Prepares data for export

### AI Model Configuration

- **Model**: GPT-4o-mini
- **Temperature**: 0.1 (for consistent, structured output)
- **Output Format**: Structured JSON for reliable parsing

## 🚀 Development Commands

The setup script creates convenient commands in the `.uv/` directory:

```bash
# Start the web interface
.uv/dev.sh

# Run system tests
.uv/test.sh

# Format code
.uv/format.sh

# Lint code
.uv/lint.sh

# Type check
.uv/typecheck.sh

# Install development dependencies
.uv/install-dev.sh

# Install test dependencies
.uv/install-test.sh
```

Or use `uv run` directly:

```bash
# Start the web interface
uv run python gladio_app.py

# Run tests
uv run python test_system.py

# Format code
uv run black .

# Lint code
uv run flake8 .

# Type check
uv run mypy .
```

## 🔧 Customization

### Modifying Analysis Criteria

Edit the system prompt in `ResumeScreenerNode` to adjust analysis focus:

```python
system_prompt = """You are an expert technical recruiter specializing in AI, automation, and software roles. 
Analyze the candidate's resume against the job description and provide a detailed screening report.

Focus on:
- Technical skill alignment
- Experience relevance
- Cultural fit indicators
- Growth potential

Be specific and reference actual content from both resume and job description."""
```

### Adding New File Formats

Extend the `TextExtractorNode` to support additional formats:

```python
def _extract_new_format(self, file_content: bytes) -> str:
    # Add your custom extraction logic here
    pass
```

### Customizing Output Schema

Modify the `ScreeningResults` and `CandidateInfo` models to add new fields:

```python
class ScreeningResults(BaseModel):
    # Add new fields here
    technical_skills_score: int = Field(description="Technical skills rating")
    experience_match: str = Field(description="Experience alignment assessment")
```

## 🚨 Troubleshooting

### Common Issues

1. **Google API Authentication Error**
   - Ensure `credentials.json` is in the project root
   - Check that Google Drive API is enabled
   - Verify OAuth 2.0 credentials are correct

2. **OpenAI API Error**
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API key permissions and billing

3. **File Processing Error**
   - Ensure the Google Drive link is accessible
   - Check file format is supported (PDF, DOCX, TXT)
   - Verify file permissions in Google Drive

4. **Text Extraction Issues**
   - Some PDFs may have image-based text (not extractable)
   - Try converting to DOCX format for better results

5. **uv Installation Issues**
   - Try installing uv manually: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Or use pip: `pip install uv`

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export DEBUG=1
uv run python gladio_app.py
```

## 📈 Performance Considerations

- **File Size**: Large files (>10MB) may take longer to process
- **API Limits**: Be mindful of OpenAI API rate limits
- **Concurrent Users**: The system handles one request at a time by default
- **Caching**: Consider implementing result caching for repeated analyses
- **uv Benefits**: Faster dependency resolution and virtual environment management

## 🔮 Future Enhancements

- **Batch Processing**: Handle multiple resumes simultaneously
- **Advanced Analytics**: Historical trend analysis and reporting
- **Integration APIs**: Direct Google Sheets export
- **Custom Models**: Fine-tuned models for specific industries
- **Multi-language Support**: International resume processing
- **ReAct Agent**: For complex reasoning scenarios

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Development Setup

```bash
# Install development dependencies
uv sync --group dev

# Run tests
uv run pytest

# Format code
uv run black .

# Type check
uv run mypy .
```

## 📞 Support

For support and questions:
1. Check the troubleshooting section above
2. Review the code comments for implementation details
3. Open an issue on the project repository 