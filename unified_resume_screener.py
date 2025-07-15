"""
Unified Resume Screening System
Professional web interface for matrix-based resume screening
"""

import os
import json
import csv
import io
import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import tempfile
import requests
import pandas as pd

import gradio as gr
from resume_screener import resume_screening_workflow, ResumeScreeningState

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class UnifiedResumeScreener:
    """Unified resume screening system with matrix processing"""
    
    def __init__(self):
        self.sample_job_description = """
AI Solutions Architect

We are seeking an experienced AI Solutions Architect to join our team. The ideal candidate will have:

Requirements:
- 5+ years of experience in AI/ML development
- Strong Python programming skills
- Experience with cloud platforms (AWS, GCP, Azure)
- Knowledge of machine learning frameworks (TensorFlow, PyTorch)
- Experience with MLOps and model deployment
- Strong communication and presentation skills
- Bachelor's degree in Computer Science or related field

Preferred:
- Experience with LangChain, LangGraph, or similar frameworks
- Knowledge of vector databases and RAG systems
- Experience with Kubernetes and containerization
- Master's degree in AI/ML or related field

Responsibilities:
- Design and implement AI/ML solutions
- Work with cross-functional teams to understand requirements
- Architect scalable AI systems
- Mentor junior developers
- Stay current with AI/ML trends and technologies
"""
    
    def extract_resumes(self, resume_input_type: str, resume_file=None, resume_text="", 
                       resume_link="", resume_csv=None) -> List[Dict[str, str]]:
        """Extract resumes based on input type"""
        resumes = []
        
        if resume_input_type == "upload_file":
            if resume_file:
                # For now, we'll store the file info - actual processing happens later
                resumes.append({
                    "type": "file",
                    "content": resume_file.name,
                    "name": resume_file.name,
                    "source": "uploaded_file"
                })
        
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
                resumes.append({
                    "type": "google_drive",
                    "content": resume_link,
                    "name": f"Google Drive: {resume_link}",
                    "source": "google_drive"
                })
        
        elif resume_input_type == "csv_links":
            if resume_csv:
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
            if jd_file:
                # For now, we'll store the file info - actual processing happens later
                job_descriptions.append({
                    "type": "file",
                    "content": jd_file.name,
                    "name": jd_file.name,
                    "source": "uploaded_file"
                })
        
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
            if jd_csv:
                try:
                    # Read CSV and extract links
                    df = pd.read_csv(jd_csv.name)
                    # Assuming first column contains links
                    link_column = df.columns[0]
                    for idx, link in enumerate(df[link_column]):
                        if pd.notna(link) and str(link).strip():
                            job_descriptions.append({
                                "type": "link",
                                "content": str(link).strip(),
                                "name": f"CSV JD {idx + 1}",
                                "source": "csv_links"
                            })
                except Exception as e:
                    raise gr.Error(f"Error reading CSV file: {str(e)}")
        
        return job_descriptions
    
    def scrape_job_description(self, url: str) -> str:
        """Scrape job description from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Basic text extraction - you can enhance this with BeautifulSoup
            text = response.text
            
            # Remove HTML tags and clean up
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text[:5000]  # Limit to first 5000 characters
            
        except Exception as e:
            raise gr.Error(f"Error scraping job description: {str(e)}")
    
    def process_single_resume_jd_pair(self, resume: Dict[str, str], job_desc: Dict[str, str]) -> Dict[str, Any]:
        """Process a single resume against a single job description"""
        try:
            # Prepare inputs for the workflow
            if resume["type"] == "google_drive":
                google_drive_link = resume["content"]
            elif resume["type"] == "text":
                # For text input, we'll create a temporary file or handle differently
                # For now, we'll use a placeholder - this needs enhancement
                google_drive_link = ""
                resume_text = resume["content"]
            else:
                # For file uploads, we'll need to handle differently
                google_drive_link = ""
                resume_text = ""
            
            if job_desc["type"] == "link":
                job_description_text = self.scrape_job_description(job_desc["content"])
            elif job_desc["type"] == "text":
                job_description_text = job_desc["content"]
            else:
                job_description_text = self.sample_job_description  # Placeholder
            
            # Initialize state
            initial_state = ResumeScreeningState(
                google_drive_link=google_drive_link,
                job_description=job_description_text,
                file_id=None,
                file_name=None,
                file_type=None,
                resume_text=None,
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
                    "error": result["error"],
                    "resume_name": resume["name"],
                    "jd_name": job_desc["name"]
                }
            
            # Format results
            screening_results = result["screening_results"]
            candidate_info = result["candidate_info"]
            
            return {
                "success": True,
                "resume_name": resume["name"],
                "resume_source": resume["source"],
                "resume_content": resume.get("content", ""),
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
                "error": f"Processing failed: {str(e)}",
                "resume_name": resume["name"],
                "jd_name": job_desc["name"]
            }
    
    def process_matrix(self, resume_input_type: str, jd_input_type: str, 
                      resume_file=None, resume_text="", resume_link="", resume_csv=None,
                      jd_file=None, jd_text="", jd_link="", jd_csv=None) -> Tuple[str, str]:
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
                    
                    # Update progress (you can add a progress callback here)
                    print(f"Processed {processed}/{total_combinations}")
            
            # Generate results table and CSV
            table_html = self.create_results_table(results)
            csv_data = self.create_csv_export(results)
            
            return table_html, csv_data
            
        except Exception as e:
            error_html = f"""
            <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px;">
                <h3>Error</h3>
                <p>{str(e)}</p>
            </div>
            """
            return error_html, ""
    
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
                <p><strong>Total Analyses:</strong> {total_results}</p>
                <p><strong>Successful:</strong> {successful_results}</p>
                <p><strong>Failed:</strong> {failed_results}</p>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background: #3498db; color: white;">
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Resume</th>
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Job Description</th>
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Analysis</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i, result in enumerate(results):
            if result.get("success", False):
                # Successful result
                candidate_info = result["candidate_info"]
                screening = result["screening_results"]
                
                html += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px; vertical-align: top;">
                            <strong>{result['resume_name']}</strong><br>
                            <small>Source: {result['resume_source']}</small><br>
                            <button onclick="showResumeDetails({i})" style="margin-top: 5px; padding: 5px 10px; background: #3498db; color: white; border: none; border-radius: 3px; cursor: pointer;">View Resume</button>
                        </td>
                        <td style="border: 1px solid #ddd; padding: 12px; vertical-align: top;">
                            <strong>{result['jd_name']}</strong><br>
                            <small>Source: {result['jd_source']}</small><br>
                            <button onclick="showJDDetails({i})" style="margin-top: 5px; padding: 5px 10px; background: #3498db; color: white; border: none; border-radius: 3px; cursor: pointer;">View JD</button>
                        </td>
                        <td style="border: 1px solid #ddd; padding: 12px; vertical-align: top;">
                            <div style="text-align: center; margin-bottom: 10px;">
                                <div style="font-size: 24px; font-weight: bold; color: #3498db;">
                                    {screening['overall_fit']}/10
                                </div>
                                <div style="font-size: 12px; color: #666;">Overall Rating</div>
                            </div>
                            <div style="font-size: 12px; margin-bottom: 5px;">
                                <strong>Risk:</strong> {screening['risk_factor']['score']}
                            </div>
                            <div style="font-size: 12px; margin-bottom: 10px;">
                                <strong>Reward:</strong> {screening['reward_factor']['score']}
                            </div>
                            <button onclick="showAnalysisDetails({i})" style="width: 100%; padding: 8px; background: #27ae60; color: white; border: none; border-radius: 3px; cursor: pointer;">View Full Analysis</button>
                        </td>
                    </tr>
                """
            else:
                # Failed result
                html += f"""
                    <tr style="background: #f8d7da;">
                        <td style="border: 1px solid #ddd; padding: 12px; vertical-align: top;">
                            <strong>{result.get('resume_name', 'Unknown')}</strong><br>
                            <small>Source: {result.get('resume_source', 'Unknown')}</small>
                        </td>
                        <td style="border: 1px solid #ddd; padding: 12px; vertical-align: top;">
                            <strong>{result.get('jd_name', 'Unknown')}</strong><br>
                            <small>Source: {result.get('jd_source', 'Unknown')}</small>
                        </td>
                        <td style="border: 1px solid #ddd; padding: 12px; vertical-align: top; color: #721c24;">
                            <strong>Error:</strong> {result.get('error', 'Unknown error')}
                        </td>
                    </tr>
                """
        
        html += """
                </tbody>
            </table>
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
                    info="Select how you want to provide resume(s)"
                )
                
                # Resume input widgets (initially hidden)
                with gr.Group(visible=True) as resume_upload_group:
                    resume_file = gr.File(
                        label="Upload Resume File",
                        file_types=[".pdf", ".docx", ".txt"],
                        file_count="single"
                    )
                
                with gr.Group(visible=False) as resume_text_group:
                    resume_text = gr.Textbox(
                        label="Paste Resume Text",
                        placeholder="Paste your resume text here...",
                        lines=10
                    )
                
                with gr.Group(visible=False) as resume_link_group:
                    resume_link = gr.Textbox(
                        label="Google Drive Link",
                        placeholder="https://drive.google.com/file/d/...",
                        info="Paste a Google Drive link to your resume"
                    )
                
                with gr.Group(visible=False) as resume_csv_group:
                    resume_csv = gr.File(
                        label="Upload CSV with Resume Links",
                        file_types=[".csv"],
                        file_count="single",
                        info="CSV file with one column containing resume links"
                    )
            
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
                with gr.Group(visible=False) as jd_upload_group:
                    jd_file = gr.File(
                        label="Upload Job Description File",
                        file_types=[".pdf", ".docx", ".txt"],
                        file_count="single"
                    )
                
                with gr.Group(visible=True) as jd_text_group:
                    jd_text = gr.Textbox(
                        label="Paste Job Description",
                        placeholder="Paste job description here...",
                        lines=10,
                        value=screener.sample_job_description
                    )
                
                with gr.Group(visible=False) as jd_link_group:
                    jd_link = gr.Textbox(
                        label="Job Description URL",
                        placeholder="https://...",
                        info="URL to job posting or description"
                    )
                
                with gr.Group(visible=False) as jd_csv_group:
                    jd_csv = gr.File(
                        label="Upload CSV with Job Description Links",
                        file_types=[".csv"],
                        file_count="single",
                        info="CSV file with one column containing job description links"
                    )
        
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
            value="",
            visible=False
        )
        
        # Event handlers for radio button changes
        def update_resume_widgets(choice):
            return {
                resume_upload_group: choice == "upload_file",
                resume_text_group: choice == "paste_text",
                resume_link_group: choice == "google_drive",
                resume_csv_group: choice == "csv_links"
            }
        
        def update_jd_widgets(choice):
            return {
                jd_upload_group: choice == "upload_file",
                jd_text_group: choice == "paste_text",
                jd_link_group: choice == "link",
                jd_csv_group: choice == "csv_links"
            }
        
        resume_input_type.change(
            fn=update_resume_widgets,
            inputs=[resume_input_type],
            outputs=[resume_upload_group, resume_text_group, resume_link_group, resume_csv_group]
        )
        
        jd_input_type.change(
            fn=update_jd_widgets,
            inputs=[jd_input_type],
            outputs=[jd_upload_group, jd_text_group, jd_link_group, jd_csv_group]
        )
        
        # Process button handler
        def process_and_display(resume_input_type, resume_file, resume_text, resume_link, resume_csv,
                               jd_input_type, jd_file, jd_text, jd_link, jd_csv):
            table_html, csv_data = screener.process_matrix(
                resume_input_type, jd_input_type, resume_file, resume_text, resume_link, resume_csv,
                jd_file, jd_text, jd_link, jd_csv
            )
            
            # Create downloadable file
            if csv_data:
                csv_filename = "resume_screening_results.csv"
                return table_html, csv_data, gr.DownloadButton(visible=True, value=(csv_filename, csv_data))
            else:
                return table_html, "", gr.DownloadButton(visible=False)
        
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