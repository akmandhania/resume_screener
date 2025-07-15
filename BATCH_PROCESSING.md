# Batch Resume Screening System

Screen a single resume against multiple job descriptions efficiently using AI-powered analysis.

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)

1. **Start the batch processing interface:**
   ```bash
   uv run python batch_gladio_app.py
   ```

2. **Open your browser** to `http://localhost:7861`

3. **Upload your resume** (PDF, DOCX, or TXT)

4. **Download the CSV template** and fill it with job URLs

5. **Upload your job URLs CSV** and click "Start Batch Screening"

### Option 2: Command Line

1. **Create a CSV file** with job URLs:
   ```csv
   Job URL
   https://www.linkedin.com/jobs/view/example1
   https://www.indeed.com/viewjob?jk=example2
   https://www.glassdoor.com/job-listing/example3
   ```

2. **Run batch processing:**
   ```bash
   uv run python batch_resume_screener.py --resume path/to/resume.pdf --input job_urls.csv --output results.csv
   ```

## 📊 Output Schema

The system generates a comprehensive CSV with the following columns:

### Job Information
- **Analysis Date**: When the screening was performed
- **Job Title**: Extracted from job posting
- **Company**: Extracted from job posting
- **Job URL**: Source URL for reference
- **Location**: Job location (if available)
- **Salary Range**: Salary range (if mentioned)

### Candidate Information
- **Candidate Name**: Full name from resume
- **Candidate Email**: Contact email
- **Resume File**: Resume filename

### Assessment Metrics
- **Overall Fit Score**: 0-10 rating
- **Risk Level**: Low/Medium/High
- **Reward Level**: Low/Medium/High
- **Recommendation**: Strong Yes/Yes/Maybe/No/Strong No

### Key Insights
- **Top 3 Strengths**: Bullet points of key strengths
- **Top 3 Concerns**: Bullet points of main concerns
- **Key Missing Skills**: Critical skills the candidate lacks
- **Years Experience Match**: How well experience aligns

### Detailed Analysis
- **Risk Explanation**: Detailed risk assessment
- **Reward Explanation**: Detailed reward assessment
- **Detailed Justification**: Complete analysis explanation

### Metadata
- **Job Description Length**: Character count for context
- **All Strengths**: Complete list of strengths
- **All Weaknesses**: Complete list of weaknesses

## 🔄 Google Sheets Workflow

### Recommended Tab Structure:

#### Tab 1: "Job Input"
```
| Job URL |
|---------|
| https://www.linkedin.com/jobs/view/example1 |
| https://www.indeed.com/viewjob?jk=example2 |
| https://www.glassdoor.com/job-listing/example3 |
```

#### Tab 2: "Screening Results"
Import the generated CSV here for detailed analysis.

#### Tab 3: "Candidate Summary"
```
| Candidate Name | Email | Resume File | Total Jobs | Avg Score | Top Recommendations |
|----------------|-------|-------------|------------|-----------|-------------------|
| John Smith | john@email.com | resume.pdf | 25 | 7.2 | 5 Strong Yes, 8 Yes |
```

## 🎯 Use Cases

### For Job Seekers
- **Mass Applications**: Screen your resume against 50+ job postings
- **Target Optimization**: Identify which jobs to prioritize
- **Skill Gap Analysis**: Understand what skills to develop
- **Application Strategy**: Focus on high-scoring opportunities

### For Recruiters
- **Candidate Assessment**: Evaluate one candidate against multiple roles
- **Role Matching**: Find the best role for a specific candidate
- **Pipeline Management**: Track candidate fit across different positions
- **Decision Support**: Get AI-powered insights for hiring decisions

## ⚙️ Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Performance Settings
- **Rate Limiting**: 1 second delay between jobs (respectful to APIs)
- **Batch Size**: Recommended maximum 50 jobs per batch
- **Processing Time**: ~2-3 seconds per job
- **Memory Usage**: Minimal (processes one job at a time)

## 📈 Analysis Features

### AI-Powered Insights
- **Technical Skill Alignment**: Matches resume skills to job requirements
- **Experience Relevance**: Evaluates experience level fit
- **Cultural Fit Indicators**: Assesses soft skills and company culture
- **Growth Potential**: Evaluates career progression opportunities

### Automated Extraction
- **Job Metadata**: Automatically extracts title, company, location, salary
- **Candidate Info**: Extracts name, email, and contact details
- **Skill Analysis**: Identifies missing critical skills
- **Experience Matching**: Compares required vs. actual experience

### Smart Recommendations
- **Fit Scoring**: 0-10 scale with detailed justification
- **Risk Assessment**: Low/Medium/High risk evaluation
- **Reward Potential**: Low/Medium/High reward assessment
- **Actionable Insights**: Specific recommendations for improvement

## 🔧 Troubleshooting

### Common Issues

**"Failed to scrape job"**
- Job site may have anti-scraping measures
- URL might be invalid or expired
- Try manually copying job description

**"Processing error"**
- Check OpenAI API key is valid
- Ensure resume file is readable
- Verify job description is not empty

**"No results generated"**
- Resume file might be corrupted
- Job description too short or unclear
- API rate limits exceeded

### Performance Tips
- Use PDF or DOCX files for best text extraction
- Ensure job URLs are from supported sites
- Process in smaller batches (10-20 jobs) for better reliability
- Check results periodically during long batches

## 🚀 Advanced Features

### Custom Analysis
The system can be extended to include:
- **Industry-specific scoring**: Custom weights for different fields
- **Geographic preferences**: Location-based scoring
- **Salary expectations**: Compensation alignment analysis
- **Company culture fit**: Values and culture matching

### Integration Options
- **Google Sheets API**: Direct integration with Google Sheets
- **Webhook support**: Real-time notifications
- **API endpoints**: REST API for custom integrations
- **Database storage**: Persistent result storage

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the error messages in the console
3. Ensure all dependencies are installed: `uv sync`
4. Verify your OpenAI API key is working

## 🔄 Updates

The batch processing system is actively developed. New features include:
- Enhanced job metadata extraction
- Improved AI analysis prompts
- Better error handling and recovery
- More comprehensive output schema 