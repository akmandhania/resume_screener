"""
Test script for the Resume Screening System
Tests individual components without requiring full setup
"""

import os
import json
from typing import Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from resume_screener import (
    ResumeScreeningState, 
    FileProcessorNode, 
    TextExtractorNode,
    ResumeScreenerNode,
    InfoExtractorNode,
    DataExporterNode
)

# Sample test data
SAMPLE_RESUME_TEXT = """
John Smith
Software Engineer
john.smith@email.com

EXPERIENCE
Senior Software Engineer | TechCorp | 2020-2023
- Developed AI-powered applications using Python and TensorFlow
- Led team of 5 developers in building scalable microservices
- Implemented MLOps pipelines using Docker and Kubernetes
- Reduced deployment time by 60% through automation

Software Engineer | StartupXYZ | 2018-2020
- Built REST APIs using Python Flask and PostgreSQL
- Worked with cloud platforms (AWS, GCP)
- Collaborated with cross-functional teams

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2018

SKILLS
Python, JavaScript, TensorFlow, PyTorch, AWS, GCP, Docker, Kubernetes, Flask, PostgreSQL, Git
"""

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

def test_resume_screener_node():
    """Test the AI resume screening component"""
    print("🧪 Testing ResumeScreenerNode...")
    
    try:
        screener = ResumeScreenerNode()
        
        # Create test state
        test_state = ResumeScreeningState(
            google_drive_link="test_link",
            job_description=SAMPLE_JOB_DESCRIPTION,
            file_id="test_id",
            file_name="test_resume.pdf",
            file_type="pdf",
            resume_text=SAMPLE_RESUME_TEXT,
            screening_results=None,
            candidate_info=None,
            spreadsheet_data=None,
            error=None
        )
        
        # Run screening
        result = screener(test_state)
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return False
        
        if result.get("screening_results"):
            print("✅ Resume screening completed successfully!")
            print(f"   Overall Fit Rating: {result['screening_results']['overall_fit_rating']}/10")
            print(f"   Risk Factor: {result['screening_results']['risk_factor']['score']}")
            print(f"   Reward Factor: {result['screening_results']['reward_factor']['score']}")
            return True
        else:
            print("❌ No screening results generated")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ResumeScreenerNode: {str(e)}")
        return False

def test_info_extractor_node():
    """Test the candidate information extraction component"""
    print("🧪 Testing InfoExtractorNode...")
    
    try:
        extractor = InfoExtractorNode()
        
        # Create test state
        test_state = ResumeScreeningState(
            google_drive_link="test_link",
            job_description=SAMPLE_JOB_DESCRIPTION,
            file_id="test_id",
            file_name="test_resume.pdf",
            file_type="pdf",
            resume_text=SAMPLE_RESUME_TEXT,
            screening_results=None,
            candidate_info=None,
            spreadsheet_data=None,
            error=None
        )
        
        # Run extraction
        result = extractor(test_state)
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return False
        
        if result.get("candidate_info"):
            info = result["candidate_info"]
            print("✅ Candidate info extraction completed successfully!")
            print(f"   Name: {info['first_name']} {info['last_name']}")
            print(f"   Email: {info['email_address']}")
            return True
        else:
            print("❌ No candidate info extracted")
            return False
            
    except Exception as e:
        print(f"❌ Error testing InfoExtractorNode: {str(e)}")
        return False

def test_data_exporter_node():
    """Test the data export preparation component"""
    print("🧪 Testing DataExporterNode...")
    
    try:
        exporter = DataExporterNode()
        
        # Create test state with mock data
        test_state = ResumeScreeningState(
            google_drive_link="https://drive.google.com/test",
            job_description=SAMPLE_JOB_DESCRIPTION,
            file_id="test_id",
            file_name="test_resume.pdf",
            file_type="pdf",
            resume_text=SAMPLE_RESUME_TEXT,
            screening_results={
                "candidate_strengths": ["Python experience", "Cloud platforms"],
                "candidate_weaknesses": ["Limited LangChain experience"],
                "risk_factor": {"score": "Low", "explanation": "Good technical background"},
                "reward_factor": {"score": "High", "explanation": "Strong potential"},
                "overall_fit_rating": 8,
                "justification_for_rating": "Strong technical skills with room for growth"
            },
            candidate_info={
                "first_name": "John",
                "last_name": "Smith",
                "email_address": "john.smith@email.com"
            },
            spreadsheet_data=None,
            error=None
        )
        
        # Run export preparation
        result = exporter(test_state)
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return False
        
        if result.get("spreadsheet_data"):
            data = result["spreadsheet_data"]
            print("✅ Data export preparation completed successfully!")
            print(f"   Fields prepared: {len(data)}")
            print(f"   Overall Fit: {data['Overall Fit']}")
            return True
        else:
            print("❌ No spreadsheet data prepared")
            return False
            
    except Exception as e:
        print(f"❌ Error testing DataExporterNode: {str(e)}")
        return False

def test_workflow_integration():
    """Test the complete workflow with mock data"""
    print("🧪 Testing complete workflow integration...")
    
    try:
        from resume_screener import resume_screening_workflow
        
        # Create initial state with mock data
        initial_state = ResumeScreeningState(
            google_drive_link="https://drive.google.com/test",
            job_description=SAMPLE_JOB_DESCRIPTION,
            file_id="test_id",
            file_name="test_resume.pdf",
            file_type="pdf",
            resume_text=SAMPLE_RESUME_TEXT,
            screening_results=None,
            candidate_info=None,
            spreadsheet_data=None,
            error=None
        )
        
        # Skip file processing nodes and start with text extraction
        # This simulates the workflow after file processing
        workflow_state = initial_state.copy()
        
        # Run the AI analysis nodes
        screener = ResumeScreenerNode()
        workflow_state = screener(workflow_state)
        
        if workflow_state.get("error"):
            print(f"❌ Screening error: {workflow_state['error']}")
            return False
        
        extractor = InfoExtractorNode()
        workflow_state = extractor(workflow_state)
        
        if workflow_state.get("error"):
            print(f"❌ Info extraction error: {workflow_state['error']}")
            return False
        
        exporter = DataExporterNode()
        workflow_state = exporter(workflow_state)
        
        if workflow_state.get("error"):
            print(f"❌ Export error: {workflow_state['error']}")
            return False
        
        print("✅ Complete workflow integration test passed!")
        print(f"   Final state keys: {list(workflow_state.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing workflow integration: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Resume Screening System Tests\n")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("   Some tests may fail. Set your OpenAI API key to run full tests.\n")
    
    tests = [
        ("Resume Screening", test_resume_screener_node),
        ("Info Extraction", test_info_extractor_node),
        ("Data Export", test_data_exporter_node),
        ("Workflow Integration", test_workflow_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"📋 {test_name} Test")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print("✅ PASSED\n")
            else:
                print("❌ FAILED\n")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}\n")
    
    print("📊 Test Results")
    print("-" * 40)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! The system is ready to use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
    
    print("\n💡 Next Steps:")
    print("1. Set up Google API credentials (credentials.json)")
    print("2. Configure environment variables (.env)")
    print("3. Run: python gladio_app.py")

if __name__ == "__main__":
    main() 