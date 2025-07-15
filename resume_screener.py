"""
Resume Screening System using LangGraph and Gladio
Converts the n8n workflow to a Python-based system with web interface
"""

import os
import re
from typing import TypedDict, Optional, List, Dict, Any
from urllib.parse import urlparse, parse_qs
import tempfile
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import PyPDF2
from docx import Document

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

class ResumeScreeningState(TypedDict):
    """State for the resume screening workflow"""
    # Input
    google_drive_link: str
    job_description: str
    
    # Processing
    file_id: Optional[str]
    file_name: Optional[str]
    file_type: Optional[str]
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
    """Process Google Drive link and extract file information"""
    
    def __init__(self):
        self._drive_service = None
    
    def _get_drive_service(self):
        """Initialize Google Drive service"""
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)
    
    def _extract_file_id(self, drive_link: str) -> str:
        """Extract file ID from Google Drive link"""
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
        elif '/document/d/' in drive_link:
            # Format: https://docs.google.com/document/d/FILE_ID/edit
            match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', drive_link)
            if match:
                return match.group(1)
        elif '/spreadsheets/d/' in drive_link:
            # Format: https://docs.google.com/spreadsheets/d/FILE_ID/edit
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', drive_link)
            if match:
                return match.group(1)
        
        raise ValueError(f"Invalid Google Drive link format: {drive_link[:50]}...")
    
    def __call__(self, state: ResumeScreeningState) -> ResumeScreeningState:
        """Process the Google Drive link and extract file info"""
        try:
            # If we already have resume text, skip file processing
            if state.get("resume_text"):
                return {
                    **state,
                    "file_id": None,
                    "file_name": "Direct Text Input",
                    "file_type": "text",
                    "error": None
                }
            
            # If no Google Drive link provided, return error
            if not state["google_drive_link"]:
                return {
                    **state,
                    "error": "No Google Drive link provided and no resume text available"
                }
            
            # Extract file ID from link
            file_id = self._extract_file_id(state["google_drive_link"])
            
            # Get drive service
            try:
                drive_service = self._get_drive_service()
            except FileNotFoundError:
                return {
                    **state,
                    "error": "Google Drive service not available. Please check credentials.json file."
                }
            except Exception as e:
                return {
                    **state,
                    "error": f"Google Drive service error: {str(e)}"
                }
            
            # Get file metadata
            file_metadata = drive_service.files().get(
                fileId=file_id, fields="name,mimeType"
            ).execute()
            
            file_name = file_metadata.get('name', 'Unknown')
            mime_type = file_metadata.get('mimeType', '')
            
            # Determine file type
            if 'pdf' in mime_type:
                file_type = 'pdf'
            elif 'word' in mime_type or 'document' in mime_type:
                file_type = 'docx'
            elif 'text' in mime_type:
                file_type = 'txt'
            else:
                file_type = 'unknown'
            
            return {
                **state,
                "file_id": file_id,
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
    
    def __init__(self):
        self.file_processor = FileProcessorNode()
    
    def _download_file(self, file_id: str) -> bytes:
        """Download file from Google Drive"""
        drive_service = self.file_processor._get_drive_service()
        if drive_service is None:
            raise Exception("Google Drive service not available")
            
        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        return file.getvalue()
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF"""
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX"""
        doc_file = io.BytesIO(file_content)
        doc = Document(doc_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _extract_txt_text(self, file_content: bytes) -> str:
        """Extract text from plain text file"""
        return file_content.decode('utf-8', errors='ignore')
    
    def __call__(self, state: ResumeScreeningState) -> ResumeScreeningState:
        """Extract text from the file"""
        if state.get("error"):
            return state
        
        try:
            # If we already have resume text, skip text extraction
            if state.get("resume_text"):
                return {
                    **state,
                    "error": None
                }
            
            # If no file ID, we can't extract text
            if not state.get("file_id"):
                return {
                    **state,
                    "error": "No file ID available for text extraction"
                }
            
            file_content = self._download_file(state["file_id"])
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
                    "error": f"Unsupported file type: {file_type}"
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
            
            # Prepare spreadsheet data
            spreadsheet_data = {
                "Date": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "Resume": state["google_drive_link"],
                "First Name": state["candidate_info"]["first_name"],
                "Last Name": state["candidate_info"]["last_name"],
                "Email": state["candidate_info"]["email_address"],
                "Strengths": "\n\n".join(state["screening_results"]["candidate_strengths"]),
                "Weaknesses": "\n\n".join(state["screening_results"]["candidate_weaknesses"]),
                "Risk Factor": f"{state['screening_results']['risk_factor']['score']}\n\n{state['screening_results']['risk_factor']['explanation']}",
                "Reward Factor": f"{state['screening_results']['reward_factor']['score']}\n\n{state['screening_results']['reward_factor']['explanation']}",
                "Justification": state["screening_results"]["justification_for_rating"],
                "Overall Fit": state["screening_results"]["overall_fit_rating"]
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
resume_screening_workflow = create_workflow() 