"""
Batch Resume Screening Web Interface
Processes a single resume against multiple job descriptions from a CSV file
"""

import os
import json
import pandas as pd
from typing import Dict, Any, List
import gradio as gr
from batch_resume_screener import BatchResumeScreener

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def create_job_input_template():
    """Create a template CSV file for job URLs input"""
    template_data = {
        'Job Title': ['AI Engineer', 'ML Scientist', 'Data Engineer', 'Software Engineer'],
        'Company': ['TechCorp', 'DataCo', 'AI Startup', 'BigTech Inc'],
        'Job URL': [
            'https://www.linkedin.com/jobs/view/example1',
            'https://www.indeed.com/viewjob?jk=example2', 
            'https://www.glassdoor.com/job-listing/example3',
            'https://www.monster.com/job/example4'
        ],
        'Location': ['Remote', 'San Francisco, CA', 'New York, NY', 'Seattle, WA'],
        'Salary Range': ['$120k-150k', '$140k-180k', '$100k-130k', '$130k-160k'],
        'Status': ['Pending', 'Pending', 'Pending', 'Pending'],
        'Notes': ['', '', '', '']
    }
    
    df = pd.DataFrame(template_data)
    template_file = "job_input_template.csv"
    df.to_csv(template_file, index=False)
    return template_file

def process_batch_screening(resume_file, job_csv_file):
    """Process batch screening and return results"""
    if not resume_file:
        return "❌ Please upload a resume file.", "No data available."
    
    if not job_csv_file:
        return "❌ Please upload a CSV file with job URLs.", "No data available."
    
    try:
        # Initialize batch screener
        screener = BatchResumeScreener()
        
        # Process the batch
        summary = screener.process_from_csv(
            resume_file.name,
            job_csv_file.name,
            "batch_screening_results.csv"
        )
        
        # Create summary display
        summary_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                Batch Screening Summary
            </h2>
            
            <div style="background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #2c3e50; margin-top: 0;">Candidate Information</h3>
                <p><strong>Name:</strong> {summary['candidate_info']['first_name']} {summary['candidate_info']['last_name']}</p>
                <p><strong>Email:</strong> {summary['candidate_info']['email_address']}</p>
                <p><strong>Resume File:</strong> {summary['resume_file']}</p>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div style="background: #d5f4e6; padding: 15px; border-radius: 5px;">
                    <h3 style="color: #27ae60; margin-top: 0;">Total Jobs</h3>
                    <div style="font-size: 32px; font-weight: bold; color: #27ae60;">
                        {summary['total_jobs']}
                    </div>
                </div>
                
                <div style="background: #d5f4e6; padding: 15px; border-radius: 5px;">
                    <h3 style="color: #27ae60; margin-top: 0;">Successful</h3>
                    <div style="font-size: 32px; font-weight: bold; color: #27ae60;">
                        {summary['successful']}
                    </div>
                </div>
                
                <div style="background: #fadbd8; padding: 15px; border-radius: 5px;">
                    <h3 style="color: #e74c3c; margin-top: 0;">Failed</h3>
                    <div style="font-size: 32px; font-weight: bold; color: #e74c3c;">
                        {summary['failed']}
                    </div>
                </div>
            </div>
            
            <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #1976d2; margin-top: 0;">Average Fit Score</h3>
                <div style="text-align: center; margin: 20px 0;">
                    <div style="font-size: 48px; font-weight: bold; color: #1976d2;">
                        {summary['average_score']}/10
                    </div>
                </div>
            </div>
        """
        
        # Add top recommendations if available
        if summary['top_recommendations']:
            recommendations_html = """
            <div style="background: #fef9e7; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #f39c12; margin-top: 0;">🏆 Top Recommendations</h3>
                <div style="display: grid; gap: 10px;">
            """
            
            for i, rec in enumerate(summary['top_recommendations'], 1):
                recommendations_html += f"""
                <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #f39c12;">
                    <div style="font-weight: bold; color: #2c3e50;">{i}. {rec['Job Title']}</div>
                    <div style="color: #7f8c8d;">{rec['Company']}</div>
                    <div style="color: #f39c12; font-weight: bold;">Score: {rec['Score']}/10 - {rec['Recommendation']}</div>
                </div>
                """
            
            recommendations_html += "</div></div>"
            summary_html += recommendations_html
        
        summary_html += """
        <div style="background: #e8f8f5; padding: 15px; border-radius: 5px;">
            <h3 style="color: #16a085; margin-top: 0;">📊 Results</h3>
            <p>Detailed results have been saved to <strong>batch_screening_results.csv</strong></p>
            <p>You can import this CSV into Google Sheets for further analysis.</p>
        </div>
        </div>
        """
        
        # Create CSV preview
        try:
            df = pd.read_csv("batch_screening_results.csv")
            csv_preview_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
                <h3 style="color: #2c3e50;">CSV Export Preview (First 5 rows)</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; overflow-x: auto;">
                    {df.head().to_html(index=False, classes='table table-striped', border=0)}
                </div>
                <p style="margin-top: 10px; color: #6c757d; font-size: 14px;">
                    Full results saved to: batch_screening_results.csv
                </p>
            </div>
            """
        except Exception as e:
            csv_preview_html = f"Error reading CSV preview: {str(e)}"
        
        return summary_html, csv_preview_html
        
    except Exception as e:
        error_html = f"""
        <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px;">
            <h3>Error</h3>
            <p>{str(e)}</p>
        </div>
        """
        return error_html, "No data available due to error."

def main():
    """Create the Gradio interface"""
    
    with gr.Blocks(
        title="Batch Resume Screening System",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        """
    ) as demo:
        
        gr.Markdown("""
        # 📋 Batch Resume Screening System
        
        Screen a single resume against multiple job descriptions from a CSV file.
        Perfect for job seekers applying to many positions!
        
        ---
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Input Files")
                
                # Resume upload
                resume_input = gr.File(
                    label="Upload Resume File",
                    file_types=[".pdf", ".docx", ".txt"],
                    file_count="single"
                )
                
                # Job CSV upload
                job_csv_input = gr.File(
                    label="Upload Job URLs CSV",
                    file_types=[".csv"],
                    file_count="single"
                )
                
                # Template download button
                template_btn = gr.Button(
                    "Download CSV Template",
                    variant="secondary",
                    size="sm"
                )
                
                # Process button
                process_btn = gr.Button(
                    "Start Batch Screening",
                    variant="primary",
                    size="lg"
                )
                
                gr.Markdown("""
                ### Instructions
                1. **Upload Resume**: Upload your resume file (PDF, DOCX, or TXT)
                2. **Prepare Job URLs**: Create a CSV file with job URLs (see template below)
                3. **Upload CSV**: Upload your job URLs CSV file
                4. **Process**: Click "Start Batch Screening" to analyze all jobs
                5. **Review**: Check results and download the detailed CSV
                
                ### CSV Format
                Your CSV should have just one column:
                - **Job URL**: URL to the job posting (required)
                
                **Example:**
                ```
                Job URL
                https://www.linkedin.com/jobs/view/example1
                https://www.indeed.com/viewjob?jk=example2
                https://www.glassdoor.com/job-listing/example3
                ```
                
                **Supported Job Sites**: Indeed, Glassdoor, Monster, CareerBuilder, LinkedIn, and others
                
                **Note**: Job titles, companies, locations, and salary ranges will be automatically extracted from the job postings.
                """)
            
            with gr.Column(scale=2):
                gr.Markdown("### Results")
                
                results_display = gr.HTML(
                    label="Batch Screening Results",
                    value="<div style='text-align: center; color: #666; padding: 40px;'>Results will appear here after batch processing</div>"
                )
                
                csv_preview = gr.HTML(
                    label="CSV Export Preview",
                    value="<div style='text-align: center; color: #666; padding: 20px;'>CSV preview will appear here</div>"
                )
        
        # Handle template download
        def download_template():
            template_file = create_job_input_template()
            return template_file
        
        # Add event handlers
        template_btn.click(
            fn=download_template,
            inputs=[],
            outputs=[gr.File(label="Download Template")]
        )
        
        process_btn.click(
            fn=process_batch_screening,
            inputs=[resume_input, job_csv_input],
            outputs=[results_display, csv_preview]
        )
        
        gr.Markdown("""
        ---
        
        ### System Information
        - **Framework:** LangGraph + LangChain
        - **Interface:** Gradio (Batch Processing)
        - **AI Model:** GPT-4o-mini
        - **File Support:** PDF, DOCX, TXT, CSV
        - **Output:** CSV file ready for Google Sheets import
        
        ### Google Sheets Integration
        1. Download the CSV results file
        2. Import into Google Sheets
        3. Create multiple tabs:
           - **Tab 1**: Job Input (your original CSV)
           - **Tab 2**: Screening Results (imported CSV)
           - **Tab 3**: Summary (manual summary)
        
        ### Performance Notes
        - Processing time: ~2-3 seconds per job
        - Rate limiting: 1 second delay between jobs
        - Maximum recommended: 50 jobs per batch
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
        server_port=7861,  # Different port from simple app
        share=False,
        show_error=True
    ) 