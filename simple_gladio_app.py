"""
Simple Gladio Web Interface - No Google Cloud Setup Required
Works with direct file uploads and public Google Drive links
"""

import os
import json
from typing import Dict, Any
import gradio as gr
from simple_resume_screener import simple_resume_screening_workflow, ResumeScreeningState
from job_scraper import job_scraper

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Sample job description for testing
SAMPLE_JOB_DESCRIPTION = """
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

def _format_job_description(description: str) -> str:
    """Format job description for better readability"""
    if not description:
        return ""
    
    # Split into lines and clean up
    lines = description.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect and format different types of content
        if line.lower().startswith(('requirements:', 'qualifications:', 'responsibilities:', 'duties:', 'expectations:')):
            # Section headers
            formatted_lines.append(f'<h5 style="color: #2c3e50; margin: 15px 0 8px 0; font-weight: 600; border-bottom: 1px solid #ecf0f1; padding-bottom: 4px;">{line}</h5>')
        elif line.startswith(('-', '•', '*', '→')):
            # Bullet points
            content = line[1:].strip()
            formatted_lines.append(f'<div style="margin: 4px 0 4px 20px; position: relative;"><span style="color: #3498db; position: absolute; left: -15px;">•</span>{content}</div>')
        elif line.isupper() and len(line) > 3 and len(line) < 50:
            # Likely a section title
            formatted_lines.append(f'<h6 style="color: #34495e; margin: 12px 0 6px 0; font-weight: 500; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px;">{line}</h6>')
        elif any(keyword in line.lower() for keyword in ['experience:', 'skills:', 'education:', 'about', 'role', 'position']):
            # Subsection headers
            formatted_lines.append(f'<div style="font-weight: 600; color: #2c3e50; margin: 8px 0 4px 0;">{line}</div>')
        else:
            # Regular paragraph text
            if len(line) > 100:
                # Long paragraph - add some spacing
                formatted_lines.append(f'<p style="margin: 6px 0; text-align: justify;">{line}</p>')
            else:
                # Short line
                formatted_lines.append(f'<div style="margin: 4px 0;">{line}</div>')
    
    return '\n'.join(formatted_lines)

def _format_job_description_for_textbox(description: str) -> str:
    """Format job description for the textbox (plain text with better structure)"""
    if not description:
        return ""
    
    # Split into lines and clean up
    lines = description.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect and format different types of content
        if line.lower().startswith(('requirements:', 'qualifications:', 'responsibilities:', 'duties:', 'expectations:')):
            # Section headers - add extra spacing
            formatted_lines.append('')
            formatted_lines.append(f'=== {line.upper()} ===')
            formatted_lines.append('')
        elif line.startswith(('-', '•', '*', '→')):
            # Bullet points - ensure proper formatting
            content = line[1:].strip()
            formatted_lines.append(f'• {content}')
        elif line.isupper() and len(line) > 3 and len(line) < 50:
            # Likely a section title
            formatted_lines.append('')
            formatted_lines.append(f'--- {line} ---')
            formatted_lines.append('')
        elif any(keyword in line.lower() for keyword in ['experience:', 'skills:', 'education:', 'about', 'role', 'position']):
            # Subsection headers
            formatted_lines.append('')
            formatted_lines.append(f'**{line}**')
            formatted_lines.append('')
        else:
            # Regular paragraph text
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def scrape_job_from_url(job_url: str) -> Dict[str, Any]:
    """
    Scrape job description from a URL
    
    Args:
        job_url: URL of the job posting
    
    Returns:
        Dictionary containing scraping results
    """
    if not job_url.strip():
        return {
            "success": False,
            "error": "Please provide a job URL",
            "title": "",
            "company": "",
            "description": ""
        }
    
    try:
        success, title, description, company = job_scraper.scrape_job_description(job_url.strip())
        
        if success:
            # Clean the description
            cleaned_description = job_scraper.clean_description(description)
            return {
                "success": True,
                "error": None,
                "title": title,
                "company": company,
                "description": cleaned_description
            }
        else:
            return {
                "success": False,
                "error": description,  # description contains error message
                "title": "",
                "company": "",
                "description": ""
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error scraping job description: {str(e)}",
            "title": "",
            "company": "",
            "description": ""
        }

def run_resume_screening(file_input, drive_link: str, job_description: str) -> Dict[str, Any]:
    """
    Run the resume screening workflow
    
    Args:
        file_input: Uploaded file (Gradio file object)
        drive_link: Google Drive link (optional)
        job_description: Job description to screen against
    
    Returns:
        Dictionary containing the screening results
    """
    try:
        # Determine input method
        if file_input is not None:
            # Handle file-like object (older Gradio) or file path (newer Gradio)
            if hasattr(file_input, "read"):
                try:
                    file_content = file_input.read()
                    file_name = file_input.name
                finally:
                    # Ensure file handle is closed if it has a close method
                    if hasattr(file_input, "close"):
                        file_input.close()
            elif isinstance(file_input, str):
                file_name = file_input
                with open(file_input, "rb") as f:
                    file_content = f.read()
            else:
                # fallback for other types
                file_name = str(file_input)
                with open(file_name, "rb") as f:
                    file_content = f.read()
            file_type = file_name.split('.')[-1].lower()
        elif drive_link.strip():
            # Use Google Drive link - let the workflow handle the processing
            file_content = None
            file_name = None
            file_type = None
        else:
            return {
                "success": False,
                "error": "Please provide either a file upload or a Google Drive link",
                "results": None
            }
        
        # Map file extensions to types (only for uploaded files)
        if file_type:
            if file_type == 'pdf':
                file_type = 'pdf'
            elif file_type in ['docx', 'doc']:
                file_type = 'docx'
            elif file_type == 'txt':
                file_type = 'txt'
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_type}. Supported: PDF, DOCX, TXT",
                    "results": None
                }
        
        # Initialize state
        initial_state = ResumeScreeningState(
            file_content=file_content,
            file_name=file_name,
            file_type=file_type,
            drive_link=drive_link if drive_link.strip() else None,
            job_description=job_description,
            job_url=None,  # Will be set if job was scraped from URL
            resume_text=None,
            screening_results=None,
            candidate_info=None,
            spreadsheet_data=None,
            error=None
        )
        
        # Run the workflow
        result = simple_resume_screening_workflow.invoke(initial_state)
        
        # Check for errors
        if result.get("error"):
            return {
                "success": False,
                "error": result["error"],
                "results": None
            }
        
        # Format results for display
        screening_results = result["screening_results"]
        candidate_info = result["candidate_info"]
        
        formatted_results = {
            "success": True,
            "error": None,
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
        
        return formatted_results
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Workflow execution failed: {str(e)}",
            "results": None
        }

def create_results_display(results: Dict[str, Any]) -> str:
    """Create formatted HTML display of results"""
    if not results["success"]:
        return f"""
        <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px;">
            <h3>Error</h3>
            <p>{results['error']}</p>
        </div>
        """
    
    candidate_info = results["candidate_info"]
    screening = results["screening_results"]
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
            Resume Screening Results
        </h2>
        
        <div style="background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="color: #2c3e50; margin-top: 0;">Candidate Information</h3>
            <p><strong>Name:</strong> {candidate_info['first_name']} {candidate_info['last_name']}</p>
            <p><strong>Email:</strong> {candidate_info['email_address']}</p>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div style="background: #d5f4e6; padding: 15px; border-radius: 5px;">
                <h3 style="color: #27ae60; margin-top: 0;">Strengths</h3>
                <ul>
                    {''.join([f'<li>{strength}</li>' for strength in screening['strengths']])}
                </ul>
            </div>
            
            <div style="background: #fadbd8; padding: 15px; border-radius: 5px;">
                <h3 style="color: #e74c3c; margin-top: 0;">Weaknesses</h3>
                <ul>
                    {''.join([f'<li>{weakness}</li>' for weakness in screening['weaknesses']])}
                </ul>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div style="background: #fef9e7; padding: 15px; border-radius: 5px;">
                <h3 style="color: #f39c12; margin-top: 0;">Risk Assessment</h3>
                <p><strong>Score:</strong> {screening['risk_factor']['score']}</p>
                <p>{screening['risk_factor']['explanation']}</p>
            </div>
            
            <div style="background: #e8f8f5; padding: 15px; border-radius: 5px;">
                <h3 style="color: #16a085; margin-top: 0;">Reward Assessment</h3>
                <p><strong>Score:</strong> {screening['reward_factor']['score']}</p>
                <p>{screening['reward_factor']['explanation']}</p>
            </div>
        </div>
        
        <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="color: #1976d2; margin-top: 0;">Overall Assessment</h3>
            <div style="text-align: center; margin: 20px 0;">
                <div style="font-size: 48px; font-weight: bold; color: #1976d2;">
                    {screening['overall_fit']}/10
                </div>
                <div style="font-size: 18px; color: #666;">
                    Overall Fit Rating
                </div>
            </div>
            <p><strong>Justification:</strong></p>
            <p>{screening['justification']}</p>
        </div>
    </div>
    """
    
    return html

def create_spreadsheet_preview(results: Dict[str, Any]) -> str:
    """Create a preview of the data that would be exported to spreadsheet"""
    if not results["success"]:
        return "No data available due to error."
    
    spreadsheet_data = results["spreadsheet_data"]
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <h3 style="color: #2c3e50;">Spreadsheet Export Preview</h3>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #e9ecef;">
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Field</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Value</th>
                </tr>
                {''.join([f'''
                <tr>
                    <td style="border: 1px solid #dee2e6; padding: 8px; font-weight: bold;">{key}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{str(value)[:100]}{'...' if len(str(value)) > 100 else ''}</td>
                </tr>
                ''' for key, value in spreadsheet_data.items()])}
            </table>
        </div>
    </div>
    """
    
    return html

def main():
    """Create the Gradio interface"""
    
    with gr.Blocks(
        title="Simple Resume Screening System",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        """
    ) as demo:
        
        gr.Markdown("""
        # 📋 Simple Resume Screening System
        
        This system analyzes resumes against job descriptions using AI-powered screening.
        **No Google Cloud setup required!** Just upload a file or use a public Google Drive link.
        
        ---
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Input Method")
                
                # File upload option
                file_input = gr.File(
                    label="Upload Resume File",
                    file_types=[".pdf", ".docx", ".txt"],
                    file_count="single"
                )
                
                gr.Markdown("**OR**")
                
                # Google Drive link option
                drive_link = gr.Textbox(
                    label="Public Google Drive Link (Optional)",
                    placeholder="https://drive.google.com/file/d/1ee6F8VQehjRVfpguc0jtNLxIV56PO4_uQF4cDotmv-8/view",
                    lines=2,
                    value="https://drive.google.com/file/d/1ee6F8VQehjRVfpguc0jtNLxIV56PO4_uQF4cDotmv-8/view"
                )
                
                gr.Markdown("### Job Description")
                
                # Job URL input
                job_url = gr.Textbox(
                    label="Job URL (Optional)",
                    placeholder="https://www.linkedin.com/jobs/view/... or https://www.indeed.com/viewjob?jk=...",
                    lines=2
                )
                
                with gr.Row():
                    scrape_btn = gr.Button(
                        "Scrape Job Description",
                        variant="secondary",
                        size="sm"
                    )
                    clear_btn = gr.Button(
                        "Clear Preview",
                        variant="secondary",
                        size="sm"
                    )
                
                job_title = gr.Textbox(
                    label="Job Title (Auto-filled from URL)",
                    placeholder="Job title will appear here after scraping...",
                    interactive=False
                )
                
                job_description = gr.Textbox(
                    label="Job Description",
                    placeholder="Paste the job description here or scrape from a job URL...\n\nExample:\nAI Solutions Architect\n\nRequirements:\n- 5+ years of experience in AI/ML development\n- Strong Python programming skills\n- Experience with cloud platforms (AWS, GCP, Azure)\n- Knowledge of machine learning frameworks (TensorFlow, PyTorch)\n- Experience with MLOps and model deployment\n- Strong communication and presentation skills\n- Bachelor's degree in Computer Science or related field",
                    lines=12,
                    value="",
                    show_label=True,
                    container=True,
                    scale=1
                )
                
                submit_btn = gr.Button(
                    "Analyze Resume",
                    variant="primary",
                    size="lg"
                )
                
                gr.Markdown("""
                ### Instructions
                1. **Resume Input**: 
                   - **Option A**: Upload a resume file (PDF, DOCX, or TXT) - **Recommended**
                   - **Option B**: Paste a public Google Drive link
                
                2. **Job Description**:
                   - **Option A**: Paste a job posting URL and click "Scrape Job Description"
                   - **Option B**: Manually enter the job description
                
                3. **Review**: Check the scraped job description preview for accuracy
                4. **Analyze**: Click "Analyze Resume" to start the screening process
                
                **Supported Job Sites**: Indeed, Glassdoor, Monster, CareerBuilder, and others
                **LinkedIn Note**: LinkedIn may have limited scraping due to dynamic content. If scraping is incomplete, try copying the job description manually.
                **Google Drive Note**: For best results, download your Google Docs file and upload it directly. Google Drive links may have access restrictions.
                """)
            
            with gr.Column(scale=2):
                gr.Markdown("### Results")
                
                results_display = gr.HTML(
                    label="Screening Results",
                    value="<div style='text-align: center; color: #666; padding: 40px;'>Results will appear here after analysis</div>"
                )
                
                spreadsheet_preview = gr.HTML(
                    label="Spreadsheet Export Preview",
                    value="<div style='text-align: center; color: #666; padding: 20px;'>Export preview will appear here</div>"
                )
        
        # Handle job scraping
        def handle_job_scraping(job_url):
            if not job_url.strip():
                return "", "", "Please provide a job URL to scrape."
            
            result = scrape_job_from_url(job_url)
            
            if result["success"]:
                # Format the description for better readability in the textbox
                formatted_description = _format_job_description_for_textbox(result["description"])
                
                # Create a preview of the scraped content
                preview_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h3 style="color: #28a745; margin-top: 0;">✅ Successfully Scraped Job Description</h3>
                    <p><strong>Source URL:</strong> {job_url}</p>
                    <p><strong>Job Title:</strong> {result["title"]}</p>
                    <p><strong>Company:</strong> {result["company"]}</p>
                    <p><strong>Description Length:</strong> {len(result["description"])} characters</p>
                    
                    <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #ced4da; margin-top: 15px;">
                        <h4 style="color: #495057; margin-top: 0;">Scraped & Cleaned Job Description:</h4>
                        <div style="max-height: 300px; overflow-y: auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
{_format_job_description(result["description"])}
                        </div>
                    </div>
                    
                    <p style="margin-top: 15px; color: #6c757d; font-size: 14px;">
                        <strong>Next Steps:</strong> Review the description above, edit if needed, then click "Analyze Resume" to proceed with screening.
                    </p>
                </div>
                """
                return result["title"], formatted_description, preview_html
            else:
                error_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f8d7da; border-radius: 8px; border: 1px solid #f5c6cb;">
                    <h3 style="color: #721c24; margin-top: 0;">❌ Error Scraping Job Description</h3>
                    <p><strong>Source URL:</strong> {job_url}</p>
                    <p><strong>Error:</strong> {result['error']}</p>
                    <p style="margin-top: 15px; color: #721c24; font-size: 14px;">
                        Please try a different URL or manually enter the job description.
                    </p>
                </div>
                """
                return "", "", error_html
        
        # Handle form submission
        def process_screening(file_input, drive_link, job_desc):
            if not file_input and not drive_link.strip():
                return (
                    "<div style='color: red; padding: 20px; border: 1px solid red; border-radius: 5px;'>Please provide either a file upload or a Google Drive link.</div>",
                    "No data available."
                )
            
            if not job_desc.strip():
                return (
                    "<div style='color: red; padding: 20px; border: 1px solid red; border-radius: 5px;'>Please provide a job description.</div>",
                    "No data available."
                )
            
            results = run_resume_screening(file_input, drive_link, job_desc)
            results_html = create_results_display(results)
            spreadsheet_html = create_spreadsheet_preview(results)
            
            return results_html, spreadsheet_html
        
        # Clear preview function
        def clear_preview():
            return "", "", "<div style='text-align: center; color: #666; padding: 40px;'>Results will appear here after analysis</div>"
        
        # Add event handlers
        scrape_btn.click(
            fn=handle_job_scraping,
            inputs=[job_url],
            outputs=[job_title, job_description, results_display]
        )
        
        clear_btn.click(
            fn=clear_preview,
            inputs=[],
            outputs=[job_title, job_description, results_display]
        )
        
        submit_btn.click(
            fn=process_screening,
            inputs=[file_input, drive_link, job_description],
            outputs=[results_display, spreadsheet_preview]
        )
        
        gr.Markdown("""
        ---
        
        ### System Information
        - **Framework:** LangGraph + LangChain
        - **Interface:** Gradio (Gladio-compatible)
        - **AI Model:** GPT-4o-mini
        - **File Support:** PDF, DOCX, TXT
        - **Setup:** No Google Cloud required!
        
        ### Setup Requirements
        1. Install dependencies: `uv sync`
        2. Set OpenAI API key in environment
        3. Run: `uv run python simple_gladio_app.py`
        
        ### Google Drive Setup (Optional)
        If using Google Drive links:
        1. Upload your resume to Google Drive
        2. Right-click → "Get link"
        3. Change sharing to "Anyone with the link can view"
        4. Copy the link and paste it above
        """)
    
    return demo

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key to use the AI features")
    
    # Launch the interface
    demo = main()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    ) 