"""
Unified Resume Screening System
Professional web interface for matrix-based resume screening
"""

import os
import json
import csv
import io
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import tempfile
import requests
import pandas as pd

import gradio as gr
from resume_screener import resume_screening_workflow, ResumeScreeningState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('resume_screener.log')
    ]
)
logger = logging.getLogger(__name__)

# Try to import PDF text extraction libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pypdf
        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False
        logger.warning("PDF text extraction not available. Install PyPDF2 or pypdf for PDF support.")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class UnifiedResumeScreener:
    """Unified resume screening system with matrix processing"""
    
    def __init__(self):
        pass
    
    def extract_pdf_text(self, pdf_content: str) -> str:
        """Extract text from PDF content"""
        if not PDF_AVAILABLE:
            return "PDF text extraction not available. Please install PyPDF2 or pypdf."
        
        try:
            # Create a temporary file to work with the PDF content
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_content.encode('latin-1'))  # PDF content is binary
                tmp_file_path = tmp_file.name
            
            # Extract text from PDF
            try:
                import PyPDF2
                with open(tmp_file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except ImportError:
                import pypdf
                with open(tmp_file_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            # Clean up the extracted text
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            text = text.strip()
            
            return text if text else "No text could be extracted from PDF"
            
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            return f"Error extracting PDF text: {str(e)}"
    
    def extract_resumes(self, resume_input_type: str, resume_file=None, resume_text="", 
                       resume_link="", resume_csv=None) -> List[Dict[str, str]]:
        """Extract resumes based on input type"""
        resumes = []
        
        if resume_input_type == "upload_file":
            if resume_file and hasattr(resume_file, 'name') and resume_file.name:
                # Extract file content
                try:
                    file_path = resume_file.name
                    basename = os.path.basename(file_path)
                    
                    # Check if it's a PDF file
                    if file_path.lower().endswith('.pdf'):
                        # Read PDF as binary and extract text
                        with open(file_path, 'rb') as f:
                            pdf_content = f.read()
                        extracted_text = self.extract_pdf_text(pdf_content.decode('latin-1'))
                        resumes.append({
                            "type": "file",
                            "content": extracted_text,  # Store extracted text
                            "name": basename,
                            "source": "uploaded_file"
                        })
                        logger.info(f"Extracted PDF text: {extracted_text[:100]}...")
                    else:
                        # For text files, read as text
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_content = f.read()
                        resumes.append({
                            "type": "file",
                            "content": file_content,
                            "name": basename,
                            "source": "uploaded_file"
                        })
                except Exception as e:
                    raise gr.Error(f"Error reading resume file: {str(e)}")
            else:
                raise gr.Error("Please upload a resume file")
        
        elif resume_input_type == "paste_text":
            if resume_text.strip():
                resumes.append({
                    "type": "text",
                    "content": resume_text,
                    "name": "Pasted Resume",
                    "source": "pasted_text"
                })
        
        elif resume_input_type == "google_drive":
            if resume_link.strip():
                # Try to download Google Doc as PDF first (no credentials needed)
                if '/document/d/' in resume_link:
                    try:
                        logger.info(f"Attempting to download Google Doc as PDF: {resume_link}")
                        extracted_text = self.download_google_doc_as_pdf(resume_link)
                        resumes.append({
                            "type": "text",
                            "content": extracted_text,
                            "name": f"Google Doc: {resume_link}",
                            "source": "google_doc_pdf"
                        })
                        logger.info(f"Successfully extracted Google Doc text: {len(extracted_text)} characters")
                    except Exception as e:
                        logger.error(f"Google Doc PDF download failed: {str(e)}")
                        # Fall back to API method if credentials exist
                        if os.path.exists('credentials.json'):
                            resumes.append({
                                "type": "google_drive",
                                "content": resume_link,
                                "name": f"Google Drive: {resume_link}",
                                "source": "google_drive"
                            })
                        else:
                            raise gr.Error(
                                f"Could not access Google Doc: {str(e)}\n\n"
                                "Please either:\n"
                                "1. Make sure the Google Doc is shared with 'Anyone with the link can view'\n"
                                "2. Upload the file directly using 'Upload File' option\n"
                                "3. Copy and paste the content using 'Paste Text' option"
                            )
                else:
                    # For other Google Drive files, check if credentials exist
                    if not os.path.exists('credentials.json'):
                        raise gr.Error(
                            "Google Drive API credentials not found. Please either:\n"
                            "1. Upload the file directly using 'Upload File' option\n"
                            "2. Copy and paste the content using 'Paste Text' option\n"
                            "3. Set up Google Drive API credentials (see README.md for instructions)"
                        )
                    resumes.append({
                        "type": "google_drive",
                        "content": resume_link,
                        "name": f"Google Drive: {resume_link}",
                        "source": "google_drive"
                    })
        
        elif resume_input_type == "csv_links":
            if resume_csv and hasattr(resume_csv, 'name') and resume_csv.name:
                try:
                    # Read CSV and extract links
                    df = pd.read_csv(resume_csv.name)
                    # Assuming first column contains links
                    link_column = df.columns[0]
                    for idx, link in enumerate(df[link_column]):
                        if pd.notna(link) and str(link).strip():
                            resumes.append({
                                "type": "google_drive",
                                "content": str(link).strip(),
                                "name": f"CSV Resume {idx + 1}",
                                "source": "csv_links"
                            })
                except Exception as e:
                    raise gr.Error(f"Error reading CSV file: {str(e)}")
        
        return resumes
    
    def extract_job_descriptions(self, jd_input_type: str, jd_file=None, jd_text="", 
                                jd_link="", jd_csv=None) -> List[Dict[str, str]]:
        """Extract job descriptions based on input type"""
        job_descriptions = []
        
        if jd_input_type == "upload_file":
            if jd_file and hasattr(jd_file, 'name') and jd_file.name:
                # Extract file content
                try:
                    with open(jd_file.name, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                    # Use just the basename for display
                    basename = os.path.basename(jd_file.name)
                    job_descriptions.append({
                        "type": "file",
                        "content": file_content,
                        "name": basename,
                        "source": "uploaded_file"
                    })
                except Exception as e:
                    raise gr.Error(f"Error reading job description file: {str(e)}")
            else:
                raise gr.Error("Please upload a job description file")
        
        elif jd_input_type == "paste_text":
            if jd_text.strip():
                job_descriptions.append({
                    "type": "text",
                    "content": jd_text,
                    "name": "Pasted Job Description",
                    "source": "pasted_text"
                })
        
        elif jd_input_type == "link":
            if jd_link.strip():
                job_descriptions.append({
                    "type": "link",
                    "content": jd_link,
                    "name": f"Job Description: {jd_link}",
                    "source": "link"
                })
        
        elif jd_input_type == "csv_links":
            if jd_csv and hasattr(jd_csv, 'name') and jd_csv.name:
                try:
                    # Read CSV and extract links
                    df = pd.read_csv(jd_csv.name)
                    # Assuming first column contains links
                    link_column = df.columns[0]
                    for idx, link in enumerate(df[link_column]):
                        if pd.notna(link) and str(link).strip():
                            link_str = str(link).strip()
                            if link_str.startswith("http://") or link_str.startswith("https://"):
                                job_descriptions.append({
                                    "type": "link",
                                    "content": link_str,
                                    "name": f"CSV JD {idx + 1}",
                                    "source": "csv_links"
                                })
                                logger.info(f"Added JD link from CSV: {link_str}")
                            else:
                                logger.warning(f"Skipped malformed JD link in CSV: {link_str}")
                        else:
                            logger.warning(f"Skipped empty JD link in CSV at row {idx+1}")
                except Exception as e:
                    raise gr.Error(f"Error reading CSV file: {str(e)}")
        
        return job_descriptions
    
    def download_google_doc_as_pdf(self, url: str) -> str:
        """Download Google Doc as PDF and extract text"""
        try:
            # Extract document ID from Google Doc URL
            if '/document/d/' in url:
                doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', url)
                if doc_id_match:
                    doc_id = doc_id_match.group(1)
                else:
                    raise ValueError("Invalid Google Doc URL format")
            else:
                raise ValueError("Not a Google Doc URL")
            
            # Convert to PDF export URL
            pdf_export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=pdf"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Download the PDF
            response = requests.get(pdf_export_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Check if we got a PDF (not an error page)
            if response.headers.get('content-type', '').startswith('application/pdf'):
                # Extract text from the PDF
                pdf_content = response.content
                return self.extract_pdf_text(pdf_content.decode('latin-1'))
            else:
                # If we didn't get a PDF, the document might not be publicly accessible
                raise ValueError("Google Doc is not publicly accessible. Please make sure the document is shared with 'Anyone with the link can view' permissions.")
            
        except Exception as e:
            raise gr.Error(f"Error downloading Google Doc: {str(e)}")
    
    def scrape_job_description(self, url: str) -> str:
        """Scrape job description from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Enhanced text extraction with better cleaning
            text = response.text
            
            # Remove JavaScript completely
            text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL)
            text = re.sub(r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}', ' ', text, flags=re.DOTALL)
            text = re.sub(r'window\.\w+\s*=\s*\w+\(\);', ' ', text)
            text = re.sub(r'p\.resolve\s*=\s*\w+;', ' ', text)
            text = re.sub(r'p\.reject\s*=\s*\w+;', ' ', text)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            
            # Remove common LinkedIn UI text
            text = re.sub(r'Skip to main content', ' ', text)
            text = re.sub(r'Expand search.*?current selection\.', ' ', text, flags=re.DOTALL)
            text = re.sub(r'Jobs People Learning', ' ', text)
            text = re.sub(r'Clear text', ' ', text)
            text = re.sub(r'Join now Sign in', ' ', text)
            text = re.sub(r'Apply Join or sign in to find your next job', ' ', text)
            text = re.sub(r'Join to apply for.*?role at', ' ', text)
            text = re.sub(r'Not you\?', ' ', text)
            text = re.sub(r'Remove photo', ' ', text)
            text = re.sub(r'First name Last name Email Password.*?Cookie Policy', ' ', text, flags=re.DOTALL)
            text = re.sub(r'Continue Agree & Join', ' ', text)
            text = re.sub(r'You may also apply directly on company website', ' ', text)
            text = re.sub(r'Security verification', ' ', text)
            text = re.sub(r'Already on LinkedIn\? Sign in', ' ', text)
            text = re.sub(r'\d+ hours ago', ' ', text)
            text = re.sub(r'Over \d+ applicants', ' ', text)
            text = re.sub(r'See who.*?hired for', ' ', text)
            
            # Clean up whitespace and normalize
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s\.\,\-\!\?\:\;\(\)\[\]\@\#]', ' ', text)  # Keep readable characters
            text = text.strip()
            
            # Extract meaningful content (look for job-related keywords)
            lines = text.split('.')
            meaningful_lines = []
            job_keywords = ['hiring', 'job', 'position', 'role', 'responsibilities', 'requirements', 'qualifications', 'experience', 'skills']
            
            for line in lines:
                line = line.strip()
                if len(line) > 20 and any(keyword in line.lower() for keyword in job_keywords):
                    meaningful_lines.append(line)
            
            if meaningful_lines:
                text = '. '.join(meaningful_lines)
            else:
                # Fallback: take first 1000 characters that look like text
                text = text[:1000]
            
            return text[:3000]  # Limit to first 3000 characters
            
        except Exception as e:
            raise gr.Error(f"Error scraping job description: {str(e)}")
    
    def process_single_resume_jd_pair(self, resume: Dict[str, str], job_desc: Dict[str, str]) -> Dict[str, Any]:
        """Process a single resume against a single job description"""
        try:
            # Prepare inputs for the workflow
            if resume["type"] == "google_drive":
                google_drive_link = resume["content"]
                resume_text = None
            elif resume["type"] == "text":
                # For text input, we'll create a temporary file or handle differently
                # For now, we'll use a placeholder - this needs enhancement
                google_drive_link = ""
                resume_text = resume["content"]
            elif resume["type"] == "file":
                # For file uploads, use the extracted content
                google_drive_link = ""
                resume_text = resume["content"]
            else:
                google_drive_link = ""
                resume_text = ""
            
            if job_desc["type"] == "link":
                logger.info(f"Scraping job description from link: {job_desc['content']}")
                job_description_text = self.scrape_job_description(job_desc["content"])
            elif job_desc["type"] == "text":
                job_description_text = job_desc["content"]
            elif job_desc["type"] == "file":
                job_description_text = job_desc["content"]
            else:
                raise ValueError(f"Unknown job description type: {job_desc['type']}")
            
            # Initialize state
            initial_state = ResumeScreeningState(
                google_drive_link=google_drive_link,
                job_description=job_description_text,
                file_id=None,
                file_name=None,
                file_type=None,
                resume_text=resume_text,
                screening_results=None,
                candidate_info=None,
                spreadsheet_data=None,
                error=None
            )
            
            # Run the workflow
            result = resume_screening_workflow.invoke(initial_state)
            
            if result.get("error"):
                return {
                    "success": False,
                    "error": f"{result['error']} (Resume: {resume.get('content', 'N/A')[:50]}...)",
                    "resume_name": resume["name"],
                    "jd_name": job_desc["name"]
                }
            
            # Format results
            screening_results = result["screening_results"]
            candidate_info = result["candidate_info"]
            
            # Use the resume content (now properly extracted for PDFs)
            resume_content = resume.get("content", "")
            
            return {
                "success": True,
                "resume_name": resume["name"],
                "resume_source": resume["source"],
                "resume_content": resume_content,
                "jd_name": job_desc["name"],
                "jd_source": job_desc["source"],
                "jd_content": job_description_text,
                "candidate_info": candidate_info,
                "screening_results": {
                    "strengths": screening_results["candidate_strengths"],
                    "weaknesses": screening_results["candidate_weaknesses"],
                    "risk_factor": screening_results["risk_factor"],
                    "reward_factor": screening_results["reward_factor"],
                    "overall_fit": screening_results["overall_fit_rating"],
                    "justification": screening_results["justification_for_rating"]
                },
                "spreadsheet_data": result["spreadsheet_data"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Processing failed: {str(e)} (Resume: {resume.get('content', 'N/A')[:50]}...)",
                "resume_name": resume["name"],
                "jd_name": job_desc["name"]
            }
    
    def process_matrix(self, resume_input_type: str, jd_input_type: str, 
                      resume_file=None, resume_text="", resume_link="", resume_csv=None,
                      jd_file=None, jd_text="", jd_link="", jd_csv=None) -> Tuple[str, str, str]:
        """Process the matrix of resumes against job descriptions"""
        try:
            # Extract resumes and job descriptions
            resumes = self.extract_resumes(resume_input_type, resume_file, resume_text, resume_link, resume_csv)
            job_descriptions = self.extract_job_descriptions(jd_input_type, jd_file, jd_text, jd_link, jd_csv)
            
            if not resumes:
                raise gr.Error("No resumes provided")
            if not job_descriptions:
                raise gr.Error("No job descriptions provided")
            
            # Process all combinations
            results = []
            total_combinations = len(resumes) * len(job_descriptions)
            processed = 0
            
            for resume in resumes:
                for job_desc in job_descriptions:
                    result = self.process_single_resume_jd_pair(resume, job_desc)
                    results.append(result)
                    processed += 1
                    logger.info(f"Processed {processed}/{total_combinations}")
            
            # Generate results table and CSV
            table_html = self.create_results_table(results)
            csv_data = self.create_csv_export(results)
            
            # Write CSV to a temporary file for download
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            tmp.write(csv_data.encode("utf-8"))
            tmp.close()
            csv_path = tmp.name
            
            return table_html, csv_data, csv_path
        except Exception as e:
            error_html = f"""
            <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px;">
                <h3>Error</h3>
                <p>{str(e)}</p>
            </div>
            """
            return error_html, "", ""
    
    def create_results_table(self, results: List[Dict[str, Any]]) -> str:
        """Create HTML table for results display"""
        if not results:
            return "<p>No results to display.</p>"
        
        # Summary stats
        total_results = len(results)
        successful_results = sum(1 for r in results if r.get("success", False))
        failed_results = total_results - successful_results
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                Resume Screening Results
            </h2>
            
            <div style="background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #2c3e50; margin-top: 0;">Summary</h3>
                <p><strong>Total Analyses:</strong> {total_results} | <strong>Successful:</strong> {successful_results} | <strong>Failed:</strong> {failed_results}</p>
            </div>
            
            <div style="margin-top: 20px;">
        """
        
        for i, result in enumerate(results):
            if result.get("success", False):
                # Successful result
                candidate_info = result["candidate_info"]
                screening = result["screening_results"]
                
                # Clean and format resume content
                resume_content = result.get('resume_content', 'No content available')
                if resume_content and resume_content != 'No content available':
                    # Format the content for display
                    import re
                    # Remove extra whitespace
                    resume_content = re.sub(r'\s+', ' ', resume_content)
                    resume_content = resume_content.strip()
                    # Limit length for display
                    if len(resume_content) > 2000:
                        resume_content = resume_content[:2000] + "... [Content truncated for display]"
                
                # Clean and format job description content
                jd_content = result.get('jd_content', 'No content available')
                if jd_content and jd_content != 'No content available':
                    # Remove HTML tags and JavaScript
                    import re
                    # Remove HTML tags
                    jd_content = re.sub(r'<[^>]+>', ' ', jd_content)
                    # Remove JavaScript
                    jd_content = re.sub(r'<script[^>]*>.*?</script>', ' ', jd_content, flags=re.DOTALL)
                    jd_content = re.sub(r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}', ' ', jd_content)
                    # Remove extra whitespace
                    jd_content = re.sub(r'\s+', ' ', jd_content)
                    jd_content = jd_content.strip()
                    # Limit length for display
                    if len(jd_content) > 2000:
                        jd_content = jd_content[:2000] + "... [Content truncated for display]"
                
                # Create expandable sections for details
                resume_details = f"""
                <details style="margin-top: 10px;">
                    <summary style="cursor: pointer; color: #3498db; font-weight: bold;">📄 View Resume Details</summary>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <h4>Candidate Information</h4>
                        <p><strong>Name:</strong> {candidate_info.get('first_name', 'N/A')} {candidate_info.get('last_name', 'N/A')}</p>
                        <p><strong>Email:</strong> {candidate_info.get('email_address', 'N/A')}</p>
                        <h4>Resume Content</h4>
                        <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd; max-height: 400px; overflow-y: auto; font-family: Arial, sans-serif; font-size: 13px; line-height: 1.5; white-space: pre-wrap;">{resume_content}</div>
                    </div>
                </details>
                """
                
                jd_details = f"""
                <details style="margin-top: 10px;">
                    <summary style="cursor: pointer; color: #3498db; font-weight: bold;">💼 View Job Description</summary>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <h4>Job Description Content</h4>
                        <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd; max-height: 400px; overflow-y: auto; font-family: Arial, sans-serif; font-size: 13px; line-height: 1.5; white-space: pre-wrap;">{jd_content}</div>
                    </div>
                </details>
                """
                
                # Create detailed analysis section
                strengths_html = ""
                if screening.get('strengths'):
                    strengths_html = "".join([f"<li>{s}</li>" for s in screening['strengths']])
                else:
                    strengths_html = "<li>No strengths identified</li>"
                
                weaknesses_html = ""
                if screening.get('weaknesses'):
                    weaknesses_html = "".join([f"<li>{w}</li>" for w in screening['weaknesses']])
                else:
                    weaknesses_html = "<li>No weaknesses identified</li>"
                
                analysis_details = f"""
                <details style="margin-top: 10px;">
                    <summary style="cursor: pointer; color: #27ae60; font-weight: bold;">📊 View Full Analysis</summary>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div style="background: #e8f5e8; padding: 10px; border-radius: 5px;">
                                <h4 style="color: #27ae60; margin-top: 0; font-size: 14px;">Candidate Strengths</h4>
                                <ul style="margin: 0; padding-left: 20px; font-size: 12px;">{strengths_html}</ul>
                            </div>
                            <div style="background: #ffeaea; padding: 10px; border-radius: 5px;">
                                <h4 style="color: #e74c3c; margin-top: 0; font-size: 14px;">Areas for Improvement</h4>
                                <ul style="margin: 0; padding-left: 20px; font-size: 12px;">{weaknesses_html}</ul>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div style="background: #fff3cd; padding: 10px; border-radius: 5px;">
                                <h4 style="color: #856404; margin-top: 0; font-size: 14px;">Risk Assessment</h4>
                                <p style="margin: 5px 0; font-size: 12px;"><strong>Score:</strong> {screening.get('risk_factor', {}).get('score', 'N/A')}</p>
                                <p style="margin: 5px 0; font-size: 12px;"><strong>Explanation:</strong> {screening.get('risk_factor', {}).get('explanation', 'N/A')}</p>
                            </div>
                            <div style="background: #d1ecf1; padding: 10px; border-radius: 5px;">
                                <h4 style="color: #0c5460; margin-top: 0; font-size: 14px;">Reward Assessment</h4>
                                <p style="margin: 5px 0; font-size: 12px;"><strong>Score:</strong> {screening.get('reward_factor', {}).get('score', 'N/A')}</p>
                                <p style="margin: 5px 0; font-size: 12px;"><strong>Explanation:</strong> {screening.get('reward_factor', {}).get('explanation', 'N/A')}</p>
                            </div>
                        </div>
                        <div style="background: #e3f2fd; padding: 10px; border-radius: 5px;">
                            <h4 style="color: #1976d2; margin-top: 0; font-size: 14px;">Overall Assessment</h4>
                            <p style="margin: 5px 0; font-size: 12px;"><strong>Fit Rating:</strong> <span style="font-size: 16px; font-weight: bold; color: #3498db;">{screening.get('overall_fit', 'N/A')}/10</span></p>
                            <p style="margin: 5px 0; font-size: 12px;"><strong>Justification:</strong> {screening.get('justification', 'N/A')}</p>
                        </div>
                    </div>
                </details>
                """
                
                # Determine rating color based on score
                rating = screening['overall_fit']
                if rating >= 8:
                    rating_color = "#27ae60"  # Green for high scores
                    rating_bg = "#e8f5e8"
                elif rating >= 6:
                    rating_color = "#f39c12"  # Orange for medium scores
                    rating_bg = "#fff3cd"
                else:
                    rating_color = "#e74c3c"  # Red for low scores
                    rating_bg = "#ffeaea"
                
                html += f"""
                    <div style="border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; overflow: hidden;">
                        <div style="background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd;">
                            <div style="display: grid; grid-template-columns: 1fr 1fr 120px; gap: 20px; align-items: center;">
                                <div>
                                    <strong style="color: #2c3e50;">{result['resume_name']}</strong><br>
                                    <small style="color: #666;">Source: {result['resume_source']}</small>
                                </div>
                                <div>
                                    <strong style="color: #2c3e50;">{result['jd_name']}</strong><br>
                                    <small style="color: #666;">Source: {result['jd_source']}</small>
                                </div>
                                <div style="text-align: center; background: {rating_bg}; padding: 10px; border-radius: 5px; border: 2px solid {rating_color};">
                                    <div style="font-size: 20px; font-weight: bold; color: {rating_color};">
                                        {rating}/10
                                    </div>
                                    <div style="font-size: 10px; color: #666; margin-top: 2px;">
                                        Risk: {screening['risk_factor']['score']}<br>
                                        Reward: {screening['reward_factor']['score']}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div style="padding: 15px;">
                            {resume_details}
                            {jd_details}
                            {analysis_details}
                        </div>
                    </div>
                """
            else:
                # Failed result
                html += f"""
                    <div style="border: 1px solid #e74c3c; border-radius: 8px; margin-bottom: 20px; background: #fdf2f2;">
                        <div style="background: #e74c3c; color: white; padding: 15px;">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: center;">
                                <div>
                                    <strong>{result.get('resume_name', 'Unknown')}</strong><br>
                                    <small>Source: {result.get('resume_source', 'Unknown')}</small>
                                </div>
                                <div>
                                    <strong>{result.get('jd_name', 'Unknown')}</strong><br>
                                    <small>Source: {result.get('jd_source', 'Unknown')}</small>
                                </div>
                            </div>
                        </div>
                        <div style="padding: 15px; color: #e74c3c;">
                            <strong>❌ Analysis Failed</strong><br>
                            {result.get('error', 'Unknown error')}
                        </div>
                    </div>
                """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def create_csv_export(self, results: List[Dict[str, Any]]) -> str:
        """Create CSV export data"""
        if not results:
            return ""
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Resume Name', 'Resume Source', 'Job Description Name', 'Job Description Source',
            'Candidate First Name', 'Candidate Last Name', 'Candidate Email',
            'Overall Fit Rating', 'Risk Score', 'Reward Score',
            'Strengths', 'Weaknesses', 'Risk Explanation', 'Reward Explanation', 'Justification'
        ])
        
        # Write data
        for result in results:
            if result.get("success", False):
                candidate_info = result["candidate_info"]
                screening = result["screening_results"]
                
                writer.writerow([
                    result['resume_name'],
                    result['resume_source'],
                    result['jd_name'],
                    result['jd_source'],
                    candidate_info.get('first_name', ''),
                    candidate_info.get('last_name', ''),
                    candidate_info.get('email_address', ''),
                    screening['overall_fit'],
                    screening['risk_factor']['score'],
                    screening['reward_factor']['score'],
                    '; '.join(screening['strengths']),
                    '; '.join(screening['weaknesses']),
                    screening['risk_factor']['explanation'],
                    screening['reward_factor']['explanation'],
                    screening['justification']
                ])
            else:
                writer.writerow([
                    result.get('resume_name', ''),
                    result.get('resume_source', ''),
                    result.get('jd_name', ''),
                    result.get('jd_source', ''),
                    '', '', '', '', '', '', '', '', '', '', result.get('error', '')
                ])
        
        return output.getvalue()

def create_interface():
    """Create the Gradio interface"""
    screener = UnifiedResumeScreener()
    
    with gr.Blocks(title="Unified Resume Screener", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🎯 Unified Resume Screening System")
        gr.Markdown("Professional AI-powered resume screening with matrix processing capabilities")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📄 Resume Input")
                
                # Resume input type selection
                resume_input_type = gr.Radio(
                    choices=["upload_file", "paste_text", "google_drive", "csv_links"],
                    label="Resume Input Method",
                    value="upload_file",
                    info="Select how you want to provide resume(s). Google Docs work automatically, other Drive files need API credentials."
                )
                
                # Resume input widgets (initially hidden)
                resume_file = gr.File(
                    label="Upload Resume File",
                    file_types=[".pdf", ".docx", ".txt"],
                    file_count="single",
                    visible=True
                )
                resume_text = gr.Textbox(
                    label="Paste Resume Text",
                    placeholder="Paste your resume text here...",
                    lines=10,
                    visible=False
                )
                resume_link = gr.Textbox(
                    label="Google Drive Link",
                    placeholder="https://drive.google.com/file/d/...",
                    visible=False
                )
                resume_csv = gr.File(
                    label="Upload CSV with Resume Links",
                    file_types=[".csv"],
                    file_count="single",
                    visible=False
                )
                gr.Markdown("*CSV file with one column containing resume links*", visible=False)
            
            with gr.Column():
                gr.Markdown("### 💼 Job Description Input")
                
                # Job description input type selection
                jd_input_type = gr.Radio(
                    choices=["upload_file", "paste_text", "link", "csv_links"],
                    label="Job Description Input Method",
                    value="paste_text",
                    info="Select how you want to provide job description(s)"
                )
                
                # Job description input widgets (initially hidden)
                jd_file = gr.File(
                    label="Upload Job Description File",
                    file_types=[".pdf", ".docx", ".txt"],
                    file_count="single",
                    visible=False
                )
                jd_text = gr.Textbox(
                    label="Paste Job Description",
                    placeholder="Paste job description here...",
                    lines=10,
                    visible=True
                )
                jd_link = gr.Textbox(
                    label="Job Description URL",
                    placeholder="https://...",
                    visible=False
                )
                jd_csv = gr.File(
                    label="Upload CSV with Job Description Links",
                    file_types=[".csv"],
                    file_count="single",
                    visible=False
                )
                gr.Markdown("*CSV file with one column containing job description links*", visible=False)
        
        # Instructions (collapsible)
        with gr.Accordion("📖 Instructions", open=False):
            gr.Markdown("""
            ### How to Use This Tool
            
            **Resume Input Options:**
            - **Upload File**: Upload a PDF, DOCX, or TXT resume file
            - **Paste Text**: Copy and paste resume text directly
            - **Google Drive**: Provide a Google Drive link to your resume
            - **CSV Links**: Upload a CSV file with multiple resume links (one per row)
            
            **Job Description Input Options:**
            - **Upload File**: Upload a PDF, DOCX, or TXT job description file
            - **Paste Text**: Copy and paste job description text directly
            - **Link**: Provide a URL to a job posting (will be scraped)
            - **CSV Links**: Upload a CSV file with multiple job description links (one per row)
            
            **Processing:**
            - The system will process every resume against every job description
            - Results will be displayed in a table with detailed analysis
            - You can download results as a CSV file
            """)
        
        # Process button
        process_btn = gr.Button("🚀 Start Matrix Analysis", variant="primary", size="lg")
        
        # Results
        with gr.Row():
            results_html = gr.HTML(label="Results")
            csv_output = gr.Textbox(label="CSV Export Data", visible=False)
        
        # Download button
        download_btn = gr.DownloadButton(
            label="📥 Download Results as CSV",
            visible=False
        )
        
        # Event handlers for radio button changes
        def update_resume_widgets(choice):
            return (
                gr.update(visible=choice == "upload_file"),  # resume_file
                gr.update(visible=choice == "paste_text"),   # resume_text
                gr.update(visible=choice == "google_drive"), # resume_link
                gr.update(visible=choice == "csv_links")     # resume_csv
            )
        
        def update_jd_widgets(choice):
            return (
                gr.update(visible=choice == "upload_file"),  # jd_file
                gr.update(visible=choice == "paste_text"),   # jd_text
                gr.update(visible=choice == "link"),         # jd_link
                gr.update(visible=choice == "csv_links")     # jd_csv
            )
        
        resume_input_type.change(
            fn=update_resume_widgets,
            inputs=[resume_input_type],
            outputs=[resume_file, resume_text, resume_link, resume_csv]
        )
        
        jd_input_type.change(
            fn=update_jd_widgets,
            inputs=[jd_input_type],
            outputs=[jd_file, jd_text, jd_link, jd_csv]
        )
        
        # Process button handler with real-time updates
        def process_and_display(resume_input_type, resume_file, resume_text, resume_link, resume_csv,
                               jd_input_type, jd_file, jd_text, jd_link, jd_csv):
            try:
                # Validate inputs before processing
                validation_messages = []
                
                # Check resume input
                if resume_input_type == "upload_file" and (not resume_file or not hasattr(resume_file, 'name') or not resume_file.name):
                    validation_messages.append("📄 <strong>Resume:</strong> Please upload a resume file")
                elif resume_input_type == "paste_text" and not resume_text.strip():
                    validation_messages.append("📄 <strong>Resume:</strong> Please paste resume text")
                elif resume_input_type == "google_drive" and not resume_link.strip():
                    validation_messages.append("📄 <strong>Resume:</strong> Please provide a Google Drive link")
                elif resume_input_type == "csv_links" and (not resume_csv or not hasattr(resume_csv, 'name') or not resume_csv.name):
                    validation_messages.append("📄 <strong>Resume:</strong> Please upload a CSV file with resume links")
                
                # Check job description input
                if jd_input_type == "upload_file" and (not jd_file or not hasattr(jd_file, 'name') or not jd_file.name):
                    validation_messages.append("💼 <strong>Job Description:</strong> Please upload a job description file")
                elif jd_input_type == "paste_text" and not jd_text.strip():
                    validation_messages.append("💼 <strong>Job Description:</strong> Please paste job description text")
                elif jd_input_type == "link" and not jd_link.strip():
                    validation_messages.append("💼 <strong>Job Description:</strong> Please provide a job posting URL")
                elif jd_input_type == "csv_links" and (not jd_csv or not hasattr(jd_csv, 'name') or not jd_csv.name):
                    validation_messages.append("💼 <strong>Job Description:</strong> Please upload a CSV file with job description links")
                
                # If there are validation errors, show them
                if validation_messages:
                    error_html = f"""
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 10px 0;">
                        <h3 style="color: #856404; margin-top: 0;">⚠️ Please Complete Your Input</h3>
                        <p style="color: #856404; margin-bottom: 15px;">To start the analysis, please provide:</p>
                        <ul style="color: #856404; margin: 0; padding-left: 20px;">
                            {''.join(f'<li>{msg}</li>' for msg in validation_messages)}
                        </ul>
                    </div>
                    """
                    yield error_html, "", gr.update(visible=False)
                    return
                
                # Extract resumes and job descriptions
                resumes = screener.extract_resumes(resume_input_type, resume_file, resume_text, resume_link, resume_csv)
                job_descriptions = screener.extract_job_descriptions(jd_input_type, jd_file, jd_text, jd_link, jd_csv)
                
                # Check if we have valid data after extraction
                if not resumes:
                    error_html = f"""
                    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 20px; margin: 10px 0;">
                        <h3 style="color: #721c24; margin-top: 0;">📄 No Valid Resumes Found</h3>
                        <p style="color: #721c24; margin-bottom: 10px;">Please check your resume input:</p>
                        <ul style="color: #721c24; margin: 0; padding-left: 20px;">
                            <li>Make sure the file is uploaded correctly</li>
                            <li>Ensure the Google Doc is shared with "Anyone with the link can view"</li>
                            <li>Check that the CSV file contains valid links</li>
                            <li>Verify that pasted text is not empty</li>
                        </ul>
                    </div>
                    """
                    yield error_html, "", gr.update(visible=False)
                    return
                
                if not job_descriptions:
                    error_html = f"""
                    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 20px; margin: 10px 0;">
                        <h3 style="color: #721c24; margin-top: 0;">💼 No Valid Job Descriptions Found</h3>
                        <p style="color: #721c24; margin-bottom: 10px;">Please check your job description input:</p>
                        <ul style="color: #721c24; margin: 0; padding-left: 20px;">
                            <li>Make sure the file is uploaded correctly</li>
                            <li>Ensure the job posting URL is accessible</li>
                            <li>Check that the CSV file contains valid links</li>
                            <li>Verify that pasted text is not empty</li>
                        </ul>
                    </div>
                    """
                    yield error_html, "", gr.update(visible=False)
                    return
                
                # Show analysis starting message
                total_combinations = len(resumes) * len(job_descriptions)
                start_message = f"""
                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 8px; padding: 20px; margin: 10px 0;">
                    <h3 style="color: #0c5460; margin-top: 0;">🚀 Starting Analysis</h3>
                    <p style="color: #0c5460; margin-bottom: 10px;">
                        Processing <strong>{len(resumes)} resume(s)</strong> against <strong>{len(job_descriptions)} job description(s)</strong><br>
                        Total combinations to analyze: <strong>{total_combinations}</strong>
                    </p>
                    <p style="color: #0c5460; margin: 0; font-style: italic;">This may take a few moments...</p>
                </div>
                """
                yield start_message, "", gr.update(visible=False)
                
                # Process all combinations with real-time updates
                results = []
                total_combinations = len(resumes) * len(job_descriptions)
                processed = 0
                
                for resume in resumes:
                    for job_desc in job_descriptions:
                        result = screener.process_single_resume_jd_pair(resume, job_desc)
                        results.append(result)
                        processed += 1
                        
                        # Yield intermediate results for real-time updates
                        if processed % 1 == 0:  # Update after each result
                            table_html = screener.create_results_table(results)
                            csv_data = screener.create_csv_export(results)
                            yield table_html, csv_data, gr.update(visible=False)
                
                # Final results with download button
                table_html = screener.create_results_table(results)
                csv_data = screener.create_csv_export(results)
                
                # Write CSV to a temporary file for download
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                tmp.write(csv_data.encode("utf-8"))
                tmp.close()
                csv_path = tmp.name
                
                yield table_html, csv_data, gr.update(visible=True, value=csv_path)
                
            except Exception as e:
                error_html = f"""
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 20px; margin: 10px 0;">
                    <h3 style="color: #721c24; margin-top: 0;">❌ Analysis Failed</h3>
                    <p style="color: #721c24; margin-bottom: 10px;">An unexpected error occurred during processing:</p>
                    <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px; margin: 10px 0;">
                        <code style="color: #721c24;">{str(e)}</code>
                    </div>
                    <p style="color: #721c24; margin: 0; font-size: 14px;">
                        Please check your inputs and try again. If the problem persists, try using different input methods.
                    </p>
                </div>
                """
                yield error_html, "", gr.update(visible=False)
        
        process_btn.click(
            fn=process_and_display,
            inputs=[
                resume_input_type, resume_file, resume_text, resume_link, resume_csv,
                jd_input_type, jd_file, jd_text, jd_link, jd_csv
            ],
            outputs=[results_html, csv_output, download_btn]
        )
    
    return interface

def main():
    """Main function to run the application"""
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main() 