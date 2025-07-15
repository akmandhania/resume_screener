"""
Simple Resume Screening System - No Google Cloud Setup Required
Works with direct file uploads and public Google Drive links
"""

import os
import re
import tempfile
from typing import TypedDict, Optional, List, Dict, Any
from urllib.parse import urlparse, parse_qs
import requests
import io

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
import PyPDF2
from docx import Document

class ResumeScreeningState(TypedDict):
    """State for the resume screening workflow"""
    # Input
    file_content: Optional[bytes]
    file_name: Optional[str]
    file_type: Optional[str]
    drive_link: Optional[str]
    job_description: str
    job_url: Optional[str]  # Added for tracking source URL
    
    # Processing
    resume_text: Optional[str]
    
    # AI Analysis
    screening_results: Optional[Dict[str, Any]]
    candidate_info: Optional[Dict[str, str]]
    
    # Output
    spreadsheet_data: Optional[Dict[str, Any]]
    error: Optional[str]

class ScreeningResults(BaseModel):
    """Structured output for resume screening"""
    candidate_strengths: List[str] = Field(description="List of candidate strengths matching job requirements")
    candidate_weaknesses: List[str] = Field(description="List of areas where candidate lacks alignment")
    risk_factor: Dict[str, str] = Field(description="Risk assessment with score and explanation")
    reward_factor: Dict[str, str] = Field(description="Reward assessment with score and explanation")
    overall_fit_rating: int = Field(description="Fit rating from 0-10", ge=0, le=10)
    justification_for_rating: str = Field(description="Explanation for the fit rating")

class CandidateInfo(BaseModel):
    """Extracted candidate information"""
    first_name: str = Field(description="Candidate's first name")
    last_name: str = Field(description="Candidate's last name")
    email_address: str = Field(description="Candidate's email address")

class FileProcessorNode:
    """Process uploaded files or public Google Drive links"""
    
    def _extract_file_id_from_public_link(self, drive_link: str) -> str:
        """Extract file ID from public Google Drive link"""
        # Handle different Google Drive link formats
        if '/file/d/' in drive_link:
            # Format: https://drive.google.com/file/d/FILE_ID/view
            match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', drive_link)
            if match:
                return match.group(1)
        elif 'id=' in drive_link:
            # Format: https://drive.google.com/open?id=FILE_ID
            parsed = urlparse(drive_link)
            query_params = parse_qs(parsed.query)
            if 'id' in query_params:
                return query_params['id'][0]
        
        raise ValueError("Invalid Google Drive link format")
    
    def _download_from_public_link(self, drive_link: str) -> tuple[bytes, str]:
        """Download file from public Google Drive link"""
        try:
            file_id = self._extract_file_id_from_public_link(drive_link)
            
            # For Google Docs, we need to use the correct export format
            # Try different approaches for Google Docs
            download_urls = [
                # Google Docs export as PDF
                f"https://docs.google.com/document/d/{file_id}/export?format=pdf",
                # Google Docs export as DOCX
                f"https://docs.google.com/document/d/{file_id}/export?format=docx",
                # Google Drive direct download (for regular files)
                f"https://drive.google.com/uc?export=download&id={file_id}",
                # Alternative Google Drive format
                f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            ]
            
            file_content = None
            file_type = None
            
            for i, download_url in enumerate(download_urls):
                try:
                    # Set appropriate headers for Google Docs
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    # Download the file
                    response = requests.get(download_url, headers=headers, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    # Get file content
                    file_content = response.content
                    
                    # Determine file type from URL or content type
                    if 'format=pdf' in download_url or download_url.endswith('format=pdf'):
                        file_type = 'pdf'
                    elif 'format=docx' in download_url or download_url.endswith('format=docx'):
                        file_type = 'docx'
                    else:
                        # Try to determine from content type
                        content_type = response.headers.get('content-type', '').lower()
                        if 'pdf' in content_type:
                            file_type = 'pdf'
                        elif 'word' in content_type or 'document' in content_type or 'docx' in content_type:
                            file_type = 'docx'
                        elif 'text' in content_type:
                            file_type = 'txt'
                        else:
                            # Default to PDF for Google Docs
                            file_type = 'pdf'
                    
                    # If we got content, break out of the loop
                    if file_content and len(file_content) > 100:  # Ensure we got meaningful content
                        print(f"Successfully downloaded with URL {i+1}: {download_url}")
                        break
                    else:
                        print(f"URL {i+1} returned insufficient content: {len(file_content) if file_content else 0} bytes")
                        
                except Exception as e:
                    print(f"Failed to download with URL {i+1} ({download_url}): {str(e)}")
                    continue
            
            if not file_content or not file_type:
                raise ValueError(f"Could not download file from any of the attempted URLs. File ID: {file_id}")
            
            return file_content, file_type
            
        except Exception as e:
            raise ValueError(f"Failed to download from Google Drive: {str(e)}")
    
    def __call__(self, state: ResumeScreeningState) -> ResumeScreeningState:
        """Process the file input"""
        try:
            # If we have file content, use it directly
            if state.get("file_content"):
                file_content = state["file_content"]
                file_type = state.get("file_type", "unknown")
                file_name = state.get("file_name", "uploaded_file")
            else:
                # Try to process as Google Drive link
                drive_link = state.get("drive_link", "")
                if not drive_link:
                    return {
                        **state,
                        "error": "No file content or Google Drive link provided"
                    }
                
                file_content, file_type = self._download_from_public_link(drive_link)
                file_name = f"resume.{file_type}"
            
            return {
                **state,
                "file_content": file_content,
                "file_name": file_name,
                "file_type": file_type,
                "error": None
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Error processing file: {str(e)}"
            }

class TextExtractorNode:
    """Extract text from various file formats"""
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    def _extract_txt_text(self, file_content: bytes) -> str:
        """Extract text from plain text file"""
        try:
            return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"Failed to extract text from TXT: {str(e)}")
    
    def __call__(self, state: ResumeScreeningState) -> ResumeScreeningState:
        """Extract text from the file"""
        if state.get("error"):
            return state
        
        try:
            file_content = state["file_content"]
            file_type = state["file_type"]
            
            if file_type == 'pdf':
                text = self._extract_pdf_text(file_content)
            elif file_type == 'docx':
                text = self._extract_docx_text(file_content)
            elif file_type == 'txt':
                text = self._extract_txt_text(file_content)
            else:
                return {
                    **state,
                    "error": f"Unsupported file type: {file_type}. Supported: PDF, DOCX, TXT"
                }
            
            return {
                **state,
                "resume_text": text.strip(),
                "error": None
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Error extracting text: {str(e)}"
            }

class ResumeScreenerNode:
    """AI-powered resume screening analysis"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1
        )
    
    def __call__(self, state: ResumeScreeningState) -> ResumeScreeningState:
        """Analyze resume against job description"""
        if state.get("error"):
            return state
        
        try:
            system_prompt = """You are an expert technical recruiter specializing in AI, automation, and software roles. 
            Analyze the candidate's resume against the job description and provide a detailed screening report.
            
            Focus on:
            - Technical skill alignment
            - Experience relevance
            - Cultural fit indicators
            - Growth potential
            
            Be specific and reference actual content from both resume and job description."""
            
            user_prompt = f"""Job Description:
            {state['job_description']}
            
            Candidate Resume:
            {state['resume_text']}
            
            Provide your analysis in the following JSON format:
            {{
                "candidate_strengths": ["strength1", "strength2"],
                "candidate_weaknesses": ["weakness1", "weakness2"],
                "risk_factor": {{
                    "score": "Low/Medium/High",
                    "explanation": "Risk explanation"
                }},
                "reward_factor": {{
                    "score": "Low/Medium/High", 
                    "explanation": "Reward explanation"
                }},
                "overall_fit_rating": 7,
                "justification_for_rating": "Detailed justification"
            }}"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse the JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse JSON response")
            
            return {
                **state,
                "screening_results": results,
                "error": None
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Error in resume screening: {str(e)}"
            }

class InfoExtractorNode:
    """Extract candidate contact information"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
    
    def __call__(self, state: ResumeScreeningState) -> ResumeScreeningState:
        """Extract candidate information from resume"""
        if state.get("error"):
            return state
        
        try:
            system_prompt = """Extract the candidate's contact information from the resume. 
            Return only the requested information in JSON format."""
            
            user_prompt = f"""Resume Text:
            {state['resume_text']}
            
            Extract the following information in JSON format:
            {{
                "first_name": "First Name",
                "last_name": "Last Name", 
                "email_address": "Email Address"
            }}"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse JSON response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                candidate_info = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse candidate info")
            
            return {
                **state,
                "candidate_info": candidate_info,
                "error": None
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Error extracting candidate info: {str(e)}"
            }

class DataExporterNode:
    """Prepare data for export to spreadsheet"""
    
    def __call__(self, state: ResumeScreeningState) -> ResumeScreeningState:
        """Prepare structured data for export"""
        if state.get("error"):
            return state
        
        try:
            from datetime import datetime
            import re
            
            # Extract job metadata from description
            job_metadata = self._extract_job_metadata(state['job_description'])
            
            # Create recommendation based on fit score
            fit_score = state["screening_results"]["overall_fit_rating"]
            recommendation = self._get_recommendation(fit_score)
            
            # Prepare spreadsheet data with enhanced schema
            spreadsheet_data = {
                # Job Information
                "Analysis Date": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "Job Title": job_metadata.get("title", "Unknown"),
                "Company": job_metadata.get("company", "Unknown"),
                "Job URL": state.get("job_url", ""),
                "Location": job_metadata.get("location", "Unknown"),
                "Salary Range": job_metadata.get("salary_range", "Not specified"),
                
                # Candidate Information
                "Candidate Name": f"{state['candidate_info']['first_name']} {state['candidate_info']['last_name']}",
                "Candidate Email": state["candidate_info"]["email_address"],
                "Resume File": state.get("file_name", "Unknown"),
                
                # Assessment Metrics
                "Overall Fit Score": state["screening_results"]["overall_fit_rating"],
                "Risk Level": state["screening_results"]["risk_factor"]["score"],
                "Reward Level": state["screening_results"]["reward_factor"]["score"],
                "Recommendation": recommendation,
                
                # Key Insights
                "Top 3 Strengths": "\n• ".join(state["screening_results"]["candidate_strengths"][:3]),
                "Top 3 Concerns": "\n• ".join(state["screening_results"]["candidate_weaknesses"][:3]),
                "Key Missing Skills": self._extract_missing_skills(state["screening_results"]["candidate_weaknesses"]),
                "Years Experience Match": self._extract_experience_match(state["screening_results"]["justification_for_rating"]),
                
                # Detailed Analysis
                "Risk Explanation": state["screening_results"]["risk_factor"]["explanation"],
                "Reward Explanation": state["screening_results"]["reward_factor"]["explanation"],
                "Detailed Justification": state["screening_results"]["justification_for_rating"],
                
                # Metadata
                "Job Description Length": len(state['job_description']),
                "All Strengths": "\n\n".join(state["screening_results"]["candidate_strengths"]),
                "All Weaknesses": "\n\n".join(state["screening_results"]["candidate_weaknesses"])
            }
            
            return {
                **state,
                "spreadsheet_data": spreadsheet_data,
                "error": None
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Error preparing export data: {str(e)}"
            }
    
    def _extract_job_metadata(self, job_description: str) -> Dict[str, str]:
        """Extract job metadata from description"""
        metadata = {
            "title": "Unknown",
            "company": "Unknown", 
            "location": "Unknown",
            "salary_range": "Not specified"
        }
        
        # Extract job title (usually first line or prominent)
        lines = job_description.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) < 100 and not line.startswith(('Requirements:', 'Qualifications:', 'About', 'We are')):
                metadata["title"] = line
                break
        
        # Try to extract company from the job description text
        # Look for patterns like "at Company" or "Company is seeking"
        company_patterns = [
            r'at\s+([A-Z][a-zA-Z\s&]+?)(?:\s+is|\s+seeking|\s+looking|\s+needs)',
            r'([A-Z][a-zA-Z\s&]+?)\s+is\s+seeking',
            r'([A-Z][a-zA-Z\s&]+?)\s+looking\s+for',
            r'join\s+([A-Z][a-zA-Z\s&]+?)\s+as',
            r'([A-Z][a-zA-Z\s&]+?)\s+is\s+hiring',
            r'([A-Z][a-zA-Z\s&]+?)\s+has\s+an\s+opening',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and len(company) < 50:
                    metadata["company"] = company
                    break
        

        
        # Extract location
        location_patterns = [
            r'(Remote|Hybrid|On-site)',
            r'(San Francisco|New York|NYC|Los Angeles|LA|Seattle|Austin|Boston|Chicago|Denver|Atlanta|Miami|Dallas|Houston|Phoenix|Portland|San Diego|Las Vegas|Nashville|Charlotte|Raleigh|Durham|Austin|Salt Lake City|Minneapolis|Detroit|Philadelphia|Pittsburgh|Columbus|Indianapolis|Kansas City|St\. Louis|Cleveland|Cincinnati|Milwaukee|Buffalo|Rochester|Albany|Syracuse|Binghamton|Ithaca|Rochester|Buffalo|Syracuse|Albany|Binghamton|Ithaca)',
            r'(CA|NY|TX|FL|WA|IL|PA|OH|GA|NC|VA|CO|AZ|NV|OR|TN|SC|AL|MS|LA|AR|OK|KS|NE|SD|ND|MN|IA|MO|WI|MI|IN|KY|WV|MD|DE|NJ|CT|RI|MA|VT|NH|ME|MT|ID|WY|UT|NM|AK|HI)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                metadata["location"] = match.group(1)
                break
        
        # Extract salary range
        salary_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*)\s*-\s*\$(\d{1,3}(?:,\d{3})*)\s*(?:per\s+year|annually|yearly|yr)',
            r'\$(\d{1,3}(?:,\d{3})*)\s*to\s*\$(\d{1,3}(?:,\d{3})*)\s*(?:per\s+year|annually|yearly|yr)',
            r'(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)\s*(?:per\s+year|annually|yearly|yr)',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                min_salary = match.group(1).replace(',', '')
                max_salary = match.group(2).replace(',', '')
                metadata["salary_range"] = f"${min_salary}-${max_salary}/year"
                break
        
        return metadata
    
    def _get_recommendation(self, fit_score: int) -> str:
        """Convert fit score to recommendation"""
        if fit_score >= 9:
            return "Strong Yes"
        elif fit_score >= 7:
            return "Yes"
        elif fit_score >= 5:
            return "Maybe"
        elif fit_score >= 3:
            return "No"
        else:
            return "Strong No"
    
    def _extract_missing_skills(self, weaknesses: List[str]) -> str:
        """Extract key missing skills from weaknesses"""
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'sql', 'mongodb', 'postgresql', 'redis', 'elasticsearch',
            'git', 'jenkins', 'ci/cd', 'agile', 'scrum',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'microservices', 'api', 'rest', 'graphql', 'grpc'
        ]
        
        missing_skills = []
        for weakness in weaknesses:
            weakness_lower = weakness.lower()
            for skill in skill_keywords:
                if skill in weakness_lower and skill not in missing_skills:
                    missing_skills.append(skill)
        
        return ", ".join(missing_skills[:5]) if missing_skills else "None identified"
    
    def _extract_experience_match(self, justification: str) -> str:
        """Extract experience match from justification"""
        experience_patterns = [
            r'(\d+)\s*years?\s*experience',
            r'experience\s*level.*?(\d+)\s*years',
            r'(\d+)\s*years?\s*in\s*the\s*field',
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, justification, re.IGNORECASE)
            if match:
                years = match.group(1)
                return f"{years}+ years required"
        
        return "Experience level not specified"

def create_workflow():
    """Create the LangGraph workflow"""
    
    # Create the graph
    workflow = StateGraph(ResumeScreeningState)
    
    # Add nodes
    workflow.add_node("process_file", FileProcessorNode())
    workflow.add_node("extract_text", TextExtractorNode())
    workflow.add_node("screen_resume", ResumeScreenerNode())
    workflow.add_node("extract_info", InfoExtractorNode())
    workflow.add_node("prepare_export", DataExporterNode())
    
    # Add edges
    workflow.set_entry_point("process_file")
    workflow.add_edge("process_file", "extract_text")
    workflow.add_edge("extract_text", "screen_resume")
    workflow.add_edge("screen_resume", "extract_info")
    workflow.add_edge("extract_info", "prepare_export")
    workflow.add_edge("prepare_export", END)
    
    return workflow.compile()

# Create the workflow instance
simple_resume_screening_workflow = create_workflow() 