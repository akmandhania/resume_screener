"""
Batch Resume Screening System
Processes a single resume against multiple job descriptions from a Google Sheet
"""

import os
import json
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from simple_resume_screener import simple_resume_screening_workflow, ResumeScreeningState
from job_scraper import job_scraper

class BatchResumeScreener:
    """Batch processor for screening one resume against multiple jobs"""
    
    def __init__(self):
        self.results = []
        self.candidate_info = None
        self.resume_file_name = None
    
    def process_resume_against_jobs(
        self, 
        resume_file_path: str,
        job_urls: List[str],
        output_file: str = "batch_screening_results.csv"
    ) -> Dict[str, Any]:
        """
        Process a single resume against multiple job URLs
        
        Args:
            resume_file_path: Path to the resume file
            job_urls: List of job URLs to screen against
            output_file: Output CSV file path
            
        Returns:
            Dictionary with summary results
        """
        print(f"🚀 Starting batch screening of {len(job_urls)} jobs...")
        
        # Read resume file
        with open(resume_file_path, "rb") as f:
            file_content = f.read()
        
        file_name = os.path.basename(resume_file_path)
        file_type = resume_file_path.split('.')[-1].lower()
        
        # Map file extensions to types
        if file_type == 'pdf':
            file_type = 'pdf'
        elif file_type in ['docx', 'doc']:
            file_type = 'docx'
        elif file_type == 'txt':
            file_type = 'txt'
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        self.resume_file_name = file_name
        self.results = []
        
        # Process each job URL
        for i, job_url in enumerate(job_urls, 1):
            print(f"📋 Processing job {i}/{len(job_urls)}: {job_url}")
            
            # Skip empty or invalid URLs
            if not job_url or not job_url.strip() or not job_url.startswith('http'):
                print(f"⚠️ Skipping invalid URL: {job_url}")
                self.results.append({
                    "Job URL": job_url,
                    "Status": "Invalid URL",
                    "Error": "URL is empty or invalid"
                })
                continue
            
            try:
                # Scrape job description
                print(f"🔍 Scraping job description from: {job_url}")
                success, title, description, company = job_scraper.scrape_job_description(job_url)
                
                if not success:
                    print(f"❌ Failed to scrape job {i}: {description}")
                    self.results.append({
                        "Job URL": job_url,
                        "Status": "Failed to scrape",
                        "Error": description
                    })
                    continue
                
                print(f"✅ Successfully scraped job {i}: {title} at {company}")
                print(f"📝 Description length: {len(description)} characters")
                
                # Clean the description
                cleaned_description = job_scraper.clean_description(description)
                print(f"🧹 Cleaned description length: {len(cleaned_description)} characters")
                
                # Initialize state for this job
                initial_state = ResumeScreeningState(
                    file_content=file_content,
                    file_name=file_name,
                    file_type=file_type,
                    drive_link=None,
                    job_description=cleaned_description,
                    job_url=job_url,
                    resume_text=None,
                    screening_results=None,
                    candidate_info=None,
                    spreadsheet_data=None,
                    error=None
                )
                
                # Run the workflow
                print(f"🤖 Running AI analysis for job {i}...")
                result = simple_resume_screening_workflow.invoke(initial_state)
                
                if result.get("error"):
                    print(f"❌ Error processing job {i}: {result['error']}")
                    self.results.append({
                        "Job URL": job_url,
                        "Status": "Processing error",
                        "Error": result['error']
                    })
                    continue
                
                print(f"✅ AI analysis completed for job {i}")
                
                # Store candidate info from first successful run
                if self.candidate_info is None:
                    self.candidate_info = result["candidate_info"]
                
                # Add result to list
                spreadsheet_data = result["spreadsheet_data"]
                spreadsheet_data["Company"] = company
                spreadsheet_data["Job Title"] = title  # Use the title from scraper
                self.results.append(spreadsheet_data)
                
                print(f"✅ Completed job {i}: {spreadsheet_data.get('Job Title', 'Unknown')} at {company} - Score: {spreadsheet_data.get('Overall Fit Score', 'N/A')}")
                
                # Add delay to be respectful to APIs
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Exception processing job {i}: {str(e)}")
                import traceback
                print(f"🔍 Full traceback:")
                traceback.print_exc()
                self.results.append({
                    "Job URL": job_url,
                    "Status": "Exception",
                    "Error": str(e)
                })
        
        # Create summary
        summary = self._create_summary()
        
        # Save results to CSV
        self._save_results_to_csv(output_file)
        
        # Print detailed summary
        successful = len([r for r in self.results if 'Overall Fit Score' in r])
        failed = len([r for r in self.results if 'Status' in r])
        
        print(f"\n📊 Batch Processing Summary:")
        print(f"  Total jobs in CSV: {len(job_urls)}")
        print(f"  Successfully processed: {successful}")
        print(f"  Failed/Error: {failed}")
        
        # Show details for each job
        print(f"\n📋 Job Details:")
        for i, result in enumerate(self.results, 1):
            if 'Overall Fit Score' in result:
                print(f"  {i}. ✅ {result.get('Job Title', 'Unknown')} - Score: {result.get('Overall Fit Score', 'N/A')}")
            else:
                status = result.get('Status', 'Unknown')
                error = result.get('Error', 'No error message')
                print(f"  {i}. ❌ {status} - {error}")
        
        print(f"\n🎉 Batch screening completed! Processed {successful} jobs successfully.")
        print(f"📊 Results saved to: {output_file}")
        
        return summary
    
    def _create_summary(self) -> Dict[str, Any]:
        """Create summary of batch processing results"""
        successful_results = [r for r in self.results if 'Overall Fit Score' in r]
        failed_results = [r for r in self.results if 'Status' in r and r['Status'] != 'Success']
        
        if not successful_results:
            return {
                "total_jobs": len(self.results),
                "successful": 0,
                "failed": len(failed_results),
                "average_score": 0,
                "top_recommendations": [],
                "candidate_info": self.candidate_info
            }
        
        # Calculate statistics
        scores = [r['Overall Fit Score'] for r in successful_results]
        average_score = sum(scores) / len(scores)
        
        # Get top recommendations
        recommendations = []
        for result in successful_results:
            if result.get('Recommendation') in ['Strong Yes', 'Yes']:
                recommendations.append({
                    'Job Title': result.get('Job Title', 'Unknown'),
                    'Company': result.get('Company', 'Unknown'),
                    'Score': result.get('Overall Fit Score', 0),
                    'Recommendation': result.get('Recommendation', 'Unknown')
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['Score'], reverse=True)
        
        return {
            "total_jobs": len(self.results),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "average_score": round(average_score, 2),
            "top_recommendations": recommendations[:5],
            "candidate_info": self.candidate_info,
            "resume_file": self.resume_file_name
        }
    
    def _save_results_to_csv(self, output_file: str):
        """Save results to CSV file"""
        if not self.results:
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(self.results)
        
        # Reorder columns for better readability
        column_order = [
            'Analysis Date', 'Job Title', 'Company', 'Job URL', 'Location', 'Salary Range',
            'Candidate Name', 'Candidate Email', 'Resume File',
            'Overall Fit Score', 'Risk Level', 'Reward Level', 'Recommendation',
            'Top 3 Strengths', 'Top 3 Concerns', 'Key Missing Skills', 'Years Experience Match',
            'Risk Explanation', 'Reward Explanation', 'Detailed Justification',
            'Job Description Length', 'All Strengths', 'All Weaknesses'
        ]
        
        # Only include columns that exist in the data
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        # Save to CSV
        df.to_csv(output_file, index=False)
    
    def create_google_sheets_template(self, template_file: str = "job_input_template.csv"):
        """Create a template CSV file for job URLs input"""
        template_data = {
            'Job URL': [
                'https://www.linkedin.com/jobs/view/example1',
                'https://www.indeed.com/viewjob?jk=example2', 
                'https://www.glassdoor.com/job-listing/example3',
                'https://www.monster.com/job/example4',
                'https://www.careerbuilder.com/job/example5'
            ]
        }
        
        df = pd.DataFrame(template_data)
        df.to_csv(template_file, index=False)
        print(f"📋 Template created: {template_file}")
    
    def process_from_csv(
        self, 
        resume_file_path: str,
        job_input_csv: str,
        output_file: str = "screening_results.csv"
    ) -> Dict[str, Any]:
        """
        Process resume against jobs from a CSV file
        
        Args:
            resume_file_path: Path to the resume file
            job_input_csv: CSV file with job URLs
            output_file: Output CSV file path
            
        Returns:
            Dictionary with summary results
        """
        # Read job URLs from CSV
        df = pd.read_csv(job_input_csv)
        
        print(f"📋 CSV loaded with {len(df)} rows and columns: {list(df.columns)}")
        
        # Handle different possible column names
        url_column = None
        for col in df.columns:
            if 'url' in col.lower() or 'link' in col.lower():
                url_column = col
                break
        
        if url_column is None:
            # If no URL column found, assume first column contains URLs
            url_column = df.columns[0]
            print(f"📋 No 'Job URL' column found, using first column: '{url_column}'")
        
        # Show all values in the URL column for debugging
        print(f"📋 All values in '{url_column}' column:")
        for i, url in enumerate(df[url_column], 1):
            print(f"  {i}: {url}")
        
        # Filter out empty URLs and get unique URLs
        job_urls = df[url_column].dropna().unique().tolist()
        
        print(f"📋 After filtering (dropna + unique): {len(job_urls)} URLs")
        for i, url in enumerate(job_urls, 1):
            print(f"  {i}: {url}")
        
        if not job_urls:
            raise ValueError(f"No valid job URLs found in column '{url_column}'")
        
        print(f"📋 Found {len(job_urls)} unique job URLs in {job_input_csv}")
        
        # Process the jobs
        return self.process_resume_against_jobs(resume_file_path, job_urls, output_file)

def main():
    """Example usage of the batch processor"""
    screener = BatchResumeScreener()
    
    # Create template
    screener.create_google_sheets_template()
    
    print("\n📝 Instructions:")
    print("1. Edit the generated 'job_input_template.csv' file")
    print("2. Add your job URLs to the 'Job URL' column")
    print("3. Run: python batch_resume_screener.py --resume path/to/resume.pdf --input job_input_template.csv")
    print("4. Results will be saved to 'screening_results.csv'")
    print("\n💡 Tip: You can also use any CSV with URLs in the first column or a column named 'Job URL'")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch Resume Screening")
    parser.add_argument("--resume", required=True, help="Path to resume file")
    parser.add_argument("--input", required=True, help="Path to CSV file with job URLs")
    parser.add_argument("--output", default="screening_results.csv", help="Output CSV file path")
    
    args = parser.parse_args()
    
    screener = BatchResumeScreener()
    summary = screener.process_from_csv(args.resume, args.input, args.output)
    
    print("\n📊 Summary:")
    print(f"Total jobs processed: {summary['total_jobs']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Average score: {summary['average_score']}")
    
    if summary['top_recommendations']:
        print("\n🏆 Top Recommendations:")
        for i, rec in enumerate(summary['top_recommendations'], 1):
            print(f"{i}. {rec['Job Title']} at {rec['Company']} (Score: {rec['Score']})") 