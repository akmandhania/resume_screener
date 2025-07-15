"""
Gladio Web Interface for Resume Screening System
Provides a web-based interface for the LangGraph workflow
"""

import os
import json
from typing import Dict, Any
import gradio as gr
from resume_screener import resume_screening_workflow, ResumeScreeningState

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

def run_resume_screening(google_drive_link: str, job_description: str) -> Dict[str, Any]:
    """
    Run the resume screening workflow
    
    Args:
        google_drive_link: Google Drive link to the resume
        job_description: Job description to screen against
    
    Returns:
        Dictionary containing the screening results
    """
    try:
        # Initialize state
        initial_state = ResumeScreeningState(
            google_drive_link=google_drive_link,
            job_description=job_description,
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
        title="Resume Screening System",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        """
    ) as demo:
        
        gr.Markdown("""
        # 📋 Resume Screening System
        
        This system analyzes resumes against job descriptions using AI-powered screening.
        Upload a Google Drive link to a resume and provide a job description to get started.
        
        ---
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Input")
                
                google_drive_link = gr.Textbox(
                    label="Google Drive Link to Resume",
                    placeholder="https://drive.google.com/file/d/...",
                    lines=2
                )
                
                job_description = gr.Textbox(
                    label="Job Description",
                    placeholder="Paste the job description here...",
                    lines=10,
                    value=SAMPLE_JOB_DESCRIPTION
                )
                
                submit_btn = gr.Button(
                    "Analyze Resume",
                    variant="primary",
                    size="lg"
                )
                
                gr.Markdown("""
                ### Instructions
                1. Paste a Google Drive link to the resume (PDF, DOCX, or TXT)
                2. Enter or modify the job description
                3. Click "Analyze Resume" to start the screening process
                
                **Note:** You'll need to set up Google API credentials for this to work.
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
        
        # Handle form submission
        def process_screening(drive_link, job_desc):
            if not drive_link.strip():
                return (
                    "<div style='color: red; padding: 20px; border: 1px solid red; border-radius: 5px;'>Please provide a Google Drive link.</div>",
                    "No data available."
                )
            
            if not job_desc.strip():
                return (
                    "<div style='color: red; padding: 20px; border: 1px solid red; border-radius: 5px;'>Please provide a job description.</div>",
                    "No data available."
                )
            
            results = run_resume_screening(drive_link, job_desc)
            results_html = create_results_display(results)
            spreadsheet_html = create_spreadsheet_preview(results)
            
            return results_html, spreadsheet_html
        
        submit_btn.click(
            fn=process_screening,
            inputs=[google_drive_link, job_description],
            outputs=[results_display, spreadsheet_preview]
        )
        
        gr.Markdown("""
        ---
        
        ### System Information
        - **Framework:** LangGraph + LangChain
        - **Interface:** Gradio (Gladio-compatible)
        - **AI Model:** GPT-4o-mini
        - **File Support:** PDF, DOCX, TXT
        
        ### Setup Requirements
        1. Install dependencies: `pip install -r requirements.txt`
        2. Set up Google API credentials
        3. Configure environment variables
        4. Run: `python gladio_app.py`
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