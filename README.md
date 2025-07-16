# Unified Resume Screening System

A modern, AI-powered resume screening system with matrix processing capabilities. Screen multiple resumes against multiple job descriptions with a single, unified interface. Features enhanced job title extraction, comprehensive CSV exports with job URLs, and a professional web interface.

## 🚀 Features

- **AI-Powered Analysis**: Uses GPT-4o-mini for intelligent resume screening
- **Matrix Processing**: Screen multiple resumes against multiple job descriptions
- **Flexible Input Methods**: Upload files, paste text, Google Drive links, or CSV with links
- **Multi-Format Support**: Handles PDF, DOCX, and TXT files
- **Google Drive Integration**: Direct processing from Google Drive links
- **Job Description Scraping**: Automatically extract job descriptions from URLs
- **Professional UI**: Clean, modern interface with collapsible instructions
- **Comprehensive Results**: Detailed analysis with strengths, weaknesses, risk/reward assessment
- **CSV Export**: Download complete results with job URLs for easy identification
- **Enhanced Job Title Extraction**: Automatically extracts actual job titles from job postings
- **Professional Download Interface**: Clean, clickable download buttons with proper filenames
- **LangGraph Workflow**: State-based processing with clear data flow
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

#### Run the Application
```bash
uv run python unified_resume_screener.py
```
The interface will be available at `http://localhost:7860`

## 📖 Usage Guide

### Usage Guide

The unified interface supports matrix processing of multiple resumes against multiple job descriptions:

#### Input Options

**Resumes:**
- **Upload File**: Upload PDF, DOCX, or TXT resume files
- **Paste Text**: Copy and paste resume text directly
- **Google Drive Link**: Provide a Google Drive link to your resume
- **CSV with Links**: Upload a CSV file with multiple resume links (one per row)

**Job Descriptions:**
- **Upload File**: Upload PDF, DOCX, or TXT job description files
- **Paste Text**: Copy and paste job description text directly
- **URL Link**: Provide a URL to a job posting (will be automatically scraped)
- **CSV with Links**: Upload a CSV file with multiple job description links (one per row)

#### Processing

1. **Select Input Methods**: Choose how you want to provide resumes and job descriptions
2. **Provide Data**: Upload files, paste text, or provide links based on your selection
3. **Start Analysis**: Click "Start Matrix Analysis" to process all combinations
4. **Review Results**: View the results table with detailed analysis for each combination
5. **Export Data**: Download the complete results as a CSV file

#### Results

- **Matrix Processing**: If you have 3 resumes and 3 job descriptions, you get 9 analysis results
- **Compact Table**: Each row shows resume, job description, and key metrics
- **Detailed Views**: Click "View Full Analysis" for complete breakdown
- **CSV Export**: Download all results for further analysis in Excel or Google Sheets

### Supported File Formats

- **PDF**: Direct text extraction with PyPDF2
- **DOCX**: Microsoft Word documents
- **TXT**: Plain text files

### Google Drive Link Formats

The system supports these Google Drive link formats:
- `https://drive.google.com/file/d/FILE_ID/view`
- `https://drive.google.com/open?id=FILE_ID`

### CSV Export

The system automatically generates a comprehensive CSV export with the following columns:
- Resume Name, Resume Source, Job Description Name, Job Description Source, **Job Description URL**
- Candidate First Name, Last Name, Email
- Overall Fit Rating, Risk Score, Reward Score
- Strengths, Weaknesses, Risk Explanation, Reward Explanation, Justification

**New Feature**: The CSV now includes the actual job posting URL, making it easy to identify which specific job each result corresponds to when processing multiple job descriptions.

### Example CSV Input Format

For job descriptions, create a CSV file with job URLs:
```csv
Job URL
https://www.linkedin.com/jobs/view/example1
https://www.indeed.com/viewjob?jk=example2
https://www.glassdoor.com/job-listing/example3
```
   - Upload your resume file
   - Upload your job URLs CSV file

4. **Process**: Click "Start Batch Screening" to analyze all jobs

5. **Review Results**: View summary and download detailed CSV for Google Sheets

## 🆕 Recent Improvements

### Enhanced Job Title Extraction
- **Smart Title Detection**: Automatically extracts actual job titles from job postings
- **Multiple Extraction Methods**: Uses HTML title tags, meta descriptions, and text pattern matching
- **Fallback Handling**: Gracefully handles cases where job titles can't be extracted
- **Better Identification**: Instead of "JD: linkedin.com - jobs", you now see "JD: Senior Software Engineer"

### Improved Download Experience
- **Clickable Download Buttons**: Professional download interface that's fully functional
- **Consistent Filenames**: Download button shows the same filename as the actual downloaded file
- **Proper File Handling**: Uses Gradio's DownloadButton for reliable file downloads

### Enhanced CSV Exports
- **Job URL Tracking**: CSV exports now include the actual job posting URL
- **Easy Identification**: Quickly identify which specific job each result corresponds to
- **Complete Data**: All necessary information for further analysis in Excel or Google Sheets

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
uv run python unified_resume_screener.py

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