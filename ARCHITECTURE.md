# Resume Screening System Architecture

## 🏗️ System Overview

The Resume Screening System is an AI-powered application that analyzes resumes against job descriptions using LangGraph workflows, web scraping, and GPT-4o-mini for intelligent assessment. The system supports both single resume analysis and batch processing against multiple job postings.

## 📊 Architecture Diagram

```mermaid
graph TB
    %% User Interface Layer
    subgraph "User Interface Layer"
        UI1[Simple Gradio App<br/>Port 7860]
        UI2[Batch Gradio App<br/>Port 7861]
        UI3[Full Gradio App<br/>Port 7860]
    end

    %% Input Sources
    subgraph "Input Sources"
        FILES[Resume Files<br/>PDF/DOCX/TXT]
        DRIVE[Google Drive Links<br/>Public/Private]
        JOB_URLS[Job URLs<br/>LinkedIn/Indeed/etc.]
        JOB_DESC[Manual Job Descriptions]
        CSV_IN[CSV with Job URLs<br/>Batch Processing]
    end

    %% Core Processing Layer
    subgraph "Core Processing Layer"
        subgraph "LangGraph Workflow"
            FP[FileProcessorNode<br/>Extract file info]
            TE[TextExtractorNode<br/>Extract text content]
            RS[ResumeScreenerNode<br/>AI analysis]
            IE[InfoExtractorNode<br/>Extract candidate info]
            DE[DataExporterNode<br/>Prepare export data]
        end
        
        subgraph "Job Scraping System"
            JS[Job Scraper<br/>Multi-site support]
            LI[LinkedIn Scraper]
            IN[Indeed Scraper]
            GD[Glassdoor Scraper]
            MO[Monster Scraper]
            CB[CareerBuilder Scraper]
            GEN[Generic Scraper]
        end
        
        subgraph "Batch Processing"
            BP[Batch Processor<br/>Multiple jobs]
            CSV_OUT[CSV Export<br/>Google Sheets ready]
        end
    end

    %% AI/ML Layer
    subgraph "AI/ML Layer"
        GPT[GPT-4o-mini<br/>OpenAI API]
        PROMPTS[Structured Prompts<br/>Recruiter Agent]
        ANALYSIS[AI Analysis<br/>Strengths/Weaknesses<br/>Risk/Reward Assessment<br/>Overall Fit Score]
    end

    %% Data Storage & Output
    subgraph "Data & Output"
        STATE[ResumeScreeningState<br/>TypedDict State]
        RESULTS[Structured Results<br/>JSON Format]
        SPREADSHEET[Spreadsheet Data<br/>Google Sheets Ready]
        CSV_RESULTS[CSV Results<br/>Batch Processing]
    end

    %% External Services
    subgraph "External Services"
        OPENAI[OpenAI API<br/>GPT-4o-mini]
        GOOGLE[Google APIs<br/>Drive/Sheets]
        JOB_SITES[Job Sites<br/>LinkedIn/Indeed/etc.]
    end

    %% Connections - User Interface
    UI1 --> FILES
    UI1 --> DRIVE
    UI1 --> JOB_URLS
    UI1 --> JOB_DESC
    UI2 --> FILES
    UI2 --> CSV_IN
    UI3 --> DRIVE
    UI3 --> JOB_DESC

    %% Connections - Input Processing
    FILES --> FP
    DRIVE --> FP
    JOB_URLS --> JS
    JOB_DESC --> RS
    CSV_IN --> BP

    %% Connections - Core Workflow
    FP --> TE
    TE --> RS
    RS --> IE
    IE --> DE
    DE --> STATE

    %% Connections - Job Scraping
    JS --> LI
    JS --> IN
    JS --> GD
    JS --> MO
    JS --> CB
    JS --> GEN
    LI --> JOB_SITES
    IN --> JOB_SITES
    GD --> JOB_SITES
    MO --> JOB_SITES
    CB --> JOB_SITES
    GEN --> JOB_SITES

    %% Connections - AI Processing
    RS --> GPT
    GPT --> PROMPTS
    PROMPTS --> ANALYSIS
    ANALYSIS --> RESULTS

    %% Connections - Batch Processing
    BP --> JS
    BP --> RS
    BP --> CSV_OUT
    CSV_OUT --> CSV_RESULTS

    %% Connections - External Services
    GPT --> OPENAI
    DRIVE --> GOOGLE
    CSV_RESULTS --> GOOGLE

    %% Connections - Output
    STATE --> RESULTS
    RESULTS --> SPREADSHEET
    SPREADSHEET --> GOOGLE
    CSV_RESULTS --> GOOGLE

    %% Styling
    classDef uiLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef inputLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef coreLayer fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef aiLayer fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef dataLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef externalLayer fill:#f1f8e9,stroke:#33691e,stroke-width:2px

    class UI1,UI2,UI3 uiLayer
    class FILES,DRIVE,JOB_URLS,JOB_DESC,CSV_IN inputLayer
    class FP,TE,RS,IE,DE,JS,LI,IN,GD,MO,CB,GEN,BP,CSV_OUT coreLayer
    class GPT,PROMPTS,ANALYSIS aiLayer
    class STATE,RESULTS,SPREADSHEET,CSV_RESULTS dataLayer
    class OPENAI,GOOGLE,JOB_SITES externalLayer
```

## 🔄 Data Flow

### 1. Single Resume Screening Flow

```mermaid
sequenceDiagram
    participant User
    participant GradioUI
    participant FileProcessor
    participant TextExtractor
    participant JobScraper
    participant ResumeScreener
    participant InfoExtractor
    participant DataExporter
    participant OpenAI

    User->>GradioUI: Upload resume + job description/URL
    GradioUI->>FileProcessor: Process file/Drive link
    FileProcessor->>TextExtractor: Extract text content
    TextExtractor->>JobScraper: Scrape job description (if URL)
    JobScraper->>ResumeScreener: Clean job description
    ResumeScreener->>OpenAI: Send analysis prompt
    OpenAI->>ResumeScreener: Return AI analysis
    ResumeScreener->>InfoExtractor: Extract candidate info
    InfoExtractor->>DataExporter: Prepare export data
    DataExporter->>GradioUI: Return structured results
    GradioUI->>User: Display results + spreadsheet preview
```

### 2. Batch Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant BatchUI
    participant BatchProcessor
    participant JobScraper
    participant ResumeScreener
    participant CSVExporter
    participant OpenAI

    User->>BatchUI: Upload resume + CSV with job URLs
    BatchUI->>BatchProcessor: Start batch processing
    loop For each job URL
        BatchProcessor->>JobScraper: Scrape job description
        JobScraper->>ResumeScreener: Clean job description
        ResumeScreener->>OpenAI: Send analysis prompt
        OpenAI->>ResumeScreener: Return AI analysis
        ResumeScreener->>BatchProcessor: Store results
    end
    BatchProcessor->>CSVExporter: Export all results
    CSVExporter->>BatchUI: Return CSV file
    BatchUI->>User: Download results CSV
```

## 🧩 Component Details

### 1. User Interface Components

#### Simple Gradio App (`simple_gladio_app.py`)
- **Port**: 7860
- **Features**: 
  - Direct file upload (PDF/DOCX/TXT)
  - Public Google Drive links
  - Job URL scraping
  - Manual job description input
  - Real-time results display
  - Spreadsheet export preview

#### Batch Gradio App (`batch_gladio_app.py`)
- **Port**: 7861
- **Features**:
  - Single resume upload
  - CSV template download
  - Batch job URL processing
  - Progress tracking
  - CSV results export

#### Full Gradio App (`gladio_app.py`)
- **Port**: 7860
- **Features**:
  - Google Cloud integration
  - Private Google Drive access
  - Advanced authentication

### 2. Core Processing Components

#### LangGraph Workflow (`simple_resume_screener.py`)
```python
class ResumeScreeningState(TypedDict):
    # Input
    file_content: Optional[bytes]
    file_name: Optional[str]
    file_type: Optional[str]
    drive_link: Optional[str]
    job_description: str
    job_url: Optional[str]
    
    # Processing
    resume_text: Optional[str]
    
    # AI Analysis
    screening_results: Optional[Dict[str, Any]]
    candidate_info: Optional[Dict[str, str]]
    
    # Output
    spreadsheet_data: Optional[Dict[str, Any]]
    error: Optional[str]
```

**Workflow Nodes:**
1. **FileProcessorNode**: Handles file uploads and Google Drive links
2. **TextExtractorNode**: Extracts text from PDF/DOCX/TXT files
3. **ResumeScreenerNode**: AI-powered resume analysis
4. **InfoExtractorNode**: Extracts candidate information
5. **DataExporterNode**: Prepares data for spreadsheet export

#### Job Scraping System (`job_scraper.py`)
**Supported Sites:**
- LinkedIn (with enhanced scraping)
- Indeed
- Glassdoor
- Monster
- CareerBuilder
- Generic sites

**Features:**
- Retry logic with exponential backoff
- Multiple CSS selector fallbacks
- Content cleaning and validation
- Company name extraction
- Error handling and logging

### 3. AI/ML Components

#### GPT-4o-mini Integration
- **Model**: GPT-4o-mini
- **Temperature**: 0.1 (consistent results)
- **Prompts**: Structured recruiter agent prompts
- **Output**: JSON-formatted analysis

#### Analysis Components
- **Strengths Analysis**: Identifies candidate strengths
- **Weaknesses Analysis**: Identifies areas of concern
- **Risk Assessment**: Low/Medium/High risk evaluation
- **Reward Assessment**: Low/Medium/High reward potential
- **Overall Fit Score**: 0-10 rating with justification

### 4. Data Processing Components

#### Text Extraction
- **PDF**: PyPDF2 for text extraction
- **DOCX**: python-docx for Word documents
- **TXT**: Direct text reading
- **Google Drive**: API-based file download

#### Content Cleaning
- **Job Descriptions**: Remove UI elements, clean formatting
- **Resume Text**: Extract relevant information
- **Company Names**: Parse and validate

## 🔧 Technical Stack

### Core Technologies
- **Python 3.9+**: Main programming language
- **LangGraph**: Workflow orchestration
- **LangChain**: AI/ML framework
- **Gradio**: Web interface framework
- **OpenAI GPT-4o-mini**: AI analysis engine

### Dependencies
- **File Processing**: PyPDF2, python-docx
- **Web Scraping**: requests, beautifulsoup4, lxml
- **Data Handling**: pandas, pydantic
- **Google APIs**: google-api-python-client
- **Environment**: python-dotenv

### Package Management
- **uv**: Fast Python package manager
- **pyproject.toml**: Modern Python packaging
- **uv.lock**: Dependency locking

## 🚀 Deployment Architecture

### Development Setup
```bash
# Install dependencies
uv sync

# Set environment variables
echo "OPENAI_API_KEY=your-key" > .env

# Run simple interface
uv run python simple_gladio_app.py

# Run batch interface
uv run python batch_gladio_app.py
```

### Production Considerations
- **API Rate Limiting**: Built-in delays between requests
- **Error Handling**: Comprehensive error catching and reporting
- **File Management**: Proper file handle cleanup
- **Memory Management**: Efficient state management
- **Scalability**: Stateless workflow design

## 📈 Performance Characteristics

### Processing Times
- **Single Resume**: ~2-3 seconds
- **Job Scraping**: ~1-2 seconds per job
- **AI Analysis**: ~1-2 seconds per analysis
- **Batch Processing**: ~2-3 seconds per job (with delays)

### Resource Usage
- **Memory**: Low (stateless processing)
- **CPU**: Moderate (AI processing)
- **Network**: Moderate (API calls and scraping)
- **Storage**: Minimal (temporary file processing)

### Scalability
- **Concurrent Users**: Limited by OpenAI API rate limits
- **Batch Size**: Recommended max 50 jobs per batch
- **File Size**: Limited by memory (typically <10MB)

## 🔒 Security & Privacy

### Data Handling
- **File Processing**: Temporary storage only
- **API Keys**: Environment variable storage
- **Google Drive**: Public links or OAuth2 authentication
- **Job Scraping**: Respectful rate limiting

### Privacy Considerations
- **Resume Data**: Processed in memory, not stored
- **Job Data**: Scraped content not persisted
- **Analysis Results**: User-controlled export
- **API Calls**: Secure HTTPS communication

## 🛠️ Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your-openai-api-key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### Google Drive Setup (Optional)
1. Create Google Cloud Project
2. Enable Drive and Sheets APIs
3. Create OAuth2 credentials
4. Download credentials.json

### File Permissions
- **Resume Files**: Read-only access
- **CSV Files**: Read/write for batch processing
- **Output Files**: Write access for results

This architecture provides a robust, scalable, and user-friendly resume screening system that can handle both individual and batch processing scenarios while maintaining high performance and reliability. 